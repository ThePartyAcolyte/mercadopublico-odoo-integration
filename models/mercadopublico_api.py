"""
Mercado Público API integration — ORM orchestration layer.

This AbstractModel acts as the façade between the Odoo ORM and the pure Python
services defined in the ``services/`` sub-package. It owns:

- Quota management: reading/writing rate-limit state on ``res.company``.
- Sync orchestration: coordinating API calls, field mapping, and DB writes.
- Analysis pipeline: running the scoring engine and persisting results.
- Notification dispatch: posting match notifications to Discuss channels.
- Cron entrypoints: thin wrappers invoked by ``ir.cron`` records.

Dependencies (all resolved at import time):
    services.api_client  — stateless HTTP client for v1/v2 endpoints.
    services.field_mapper — pure functions for JSON → Odoo field conversion.
    services.scoring     — pure scoring engine (keyword + category + filters).
"""
import logging
import time
from datetime import datetime, timedelta

import pytz
from markupsafe import Markup

from odoo import api, fields, models

from .services.api_client import ChileCompraApiClient
from .services.field_mapper import (
    extract_v1_items,
    extract_v2_items,
    map_quick_buy_fields_v2,
    map_tender_fields_v1,
    map_tender_status_v1,
)
from .services.scoring import FUZZY_AVAILABLE, ScoringResult, score_tender

_logger = logging.getLogger(__name__)


class MercadoPublicoAPI(models.AbstractModel):
    """
    Abstract ORM model that orchestrates all Mercado Público integration logic.

    Inherited by no concrete model — all methods are called via
    ``self.env['mercadopublico.api']``. The class is registered in the ORM
    so that ``ir.cron`` and ``ir.actions.server`` records can reference it.
    """

    _name = "mercadopublico.api"
    _description = "API de Mercado Público (v1 y v2)"

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    @api.model
    def _get_company_config(self):
        """Returns the current company record (res.company)."""
        return self.env.company

    @api.model
    def _get_api_token(self) -> str:
        """Returns the API authentication token for the current company."""
        return self.env.company.mercadopublico_api_ticket

    @api.model
    def _get_api_client(self, quota_callback=None) -> ChileCompraApiClient:
        """Returns a configured API client instance for the current company."""
        callback = quota_callback or self._on_api_request_done
        return ChileCompraApiClient(api_token=self._get_api_token(), quota_callback=callback)

    # -------------------------------------------------------------------------
    # Mutual exclusion (Sync Lock)
    # -------------------------------------------------------------------------

    @api.model
    def _acquire_sync_lock(self) -> bool:
        """
        Attempts to acquire the company-wide discovery sync lock.

        Returns:
            bool: True if the lock was successfully acquired, False if a sync
                  is already active and valid (<15 minutes old).
        """
        company = self.env.company
        now = fields.Datetime.now()
        if company.mercadopublico_is_syncing:
            if (
                company.mercadopublico_sync_start_time
                and (now - company.mercadopublico_sync_start_time) > timedelta(minutes=15)
            ):
                _logger.warning("Stale sync lock detected. Resetting lock.")
            else:
                _logger.info(
                    "Mercado Público discovery sync is currently in progress. Skipping execution."
                )
                return False
        company.sudo().write({
            "mercadopublico_is_syncing": True,
            "mercadopublico_sync_start_time": now,
        })
        return True

    @api.model
    def _release_sync_lock(self) -> None:
        """Releases the company-wide discovery sync lock."""
        self.env.company.sudo().write({
            "mercadopublico_is_syncing": False,
            "mercadopublico_sync_start_time": False,
        })

    @api.model
    def _get_next_reset_utc(self) -> datetime:
        """
        Computes the next quota reset datetime as a naive UTC datetime.

        The reset is scheduled at 00:01 Chile time on the following calendar
        day, converted to UTC. This aligns with the API provider's daily quota
        window which resets at midnight Santiago time.

        Returns:
            datetime: Naive UTC datetime for the next quota reset.
        """
        chile_tz = pytz.timezone("America/Santiago")
        now_utc = datetime.now(pytz.utc)
        now_chile = now_utc.astimezone(chile_tz)
        next_reset_chile = (now_chile + timedelta(days=1)).replace(
            hour=0, minute=1, second=0, microsecond=0
        )
        return next_reset_chile.astimezone(pytz.utc).replace(tzinfo=None)

    # -------------------------------------------------------------------------
    # Quota management
    # -------------------------------------------------------------------------

    @api.model
    def _check_quota_available(self) -> bool:
        """
        Verifies the API quota is available and increments the daily counter.

        Resets the counter if the reset datetime has passed.

        Returns:
            bool: True if the request is allowed, False if daily quota is exhausted.
        """
        company = self.env.company
        now = fields.Datetime.now()

        if not company.mercadopublico_api_reset or now >= company.mercadopublico_api_reset:
            company.sudo().write({
                "mercadopublico_api_success": 0,
                "mercadopublico_api_fail": 0,
                "mercadopublico_api_reset": self._get_next_reset_utc(),
            })

        if company.mercadopublico_api_realizados >= company.mercadopublico_api_limit:
            self._log_daily_quota_reached()
            return False

        return True

    @api.model
    def _log_daily_quota_reached(self) -> None:
        """Logs a warning when the daily quota limit is reached."""
        company = self.env.company
        unblock_at = self._get_next_reset_utc()
        _logger.warning(
            "Daily API quota reached (%d/%d). Blocking requests until %s UTC.",
            company.mercadopublico_api_realizados,
            company.mercadopublico_api_limit,
            unblock_at,
        )

    # -------------------------------------------------------------------------
    # Sync orchestration
    # -------------------------------------------------------------------------

    @api.model
    def _on_api_request_done(self, is_success: bool):
        """Fallback single-request quota callback."""
        company = self.env.company.sudo()
        if is_success:
            company.write({"mercadopublico_api_success": company.mercadopublico_api_success + 1})
        else:
            company.write({"mercadopublico_api_fail": company.mercadopublico_api_fail + 1})

    @api.model
    def sync_all(self) -> dict:
        """
        Runs a full synchronization cycle for both v1 (tenders) and v2 (quick buys).

        Returns:
            dict: Combined counts with keys 'nuevas' and 'existentes'.
        """
        res_v1 = self.sync_tenders_v1()
        res_v2 = self.sync_quick_buys_v2()
        return {
            "nuevas": res_v1.get("nuevas", 0) + res_v2.get("nuevas", 0),
            "existentes": res_v1.get("existentes", 0) + res_v2.get("existentes", 0),
        }

    @api.model
    def sync_tenders_v1(self) -> dict:
        """
        Downloads the v1 tender listing for the configured date window and
        creates new ``mercadopublico.tender`` records in state 'nuevo'.

        Respects the ``mercadopublico_sync_tenders`` toggle and the
        ``mercadopublico_keyword_organismo_favorito`` mode (excluyente queries
        each favorite agency separately).

        Returns:
            dict: Counts with keys 'nuevas' (created) and 'existentes' (skipped).
        """
        config = self._get_company_config()
        new_count, existing_count = 0, 0

        if not config.mercadopublico_sync_tenders:
            return {"nuevas": new_count, "existentes": existing_count}

        if not self._acquire_sync_lock():
            return {"nuevas": 0, "existentes": 0}

        stats = {"success": 0, "fail": 0}
        def track_quota(ok: bool):
            stats["success" if ok else "fail"] += 1

        try:
            chile_tz = pytz.timezone("America/Santiago")
            current_chile_dt = datetime.now(pytz.utc).astimezone(chile_tz)
            search_date_str = (
                current_chile_dt - timedelta(days=config.mercadopublico_search_days_backward)
            ).strftime("%d%m%Y")
            _logger.info("Starting v1 tender sync for date: %s (Chile time).", search_date_str)

            client = self._get_api_client(quota_callback=track_quota)
            raw_records: list = []
            agency_filter_mode = config.mercadopublico_keyword_organismo_favorito

            if agency_filter_mode == "excluyente":
                favorite_agencies = self.env["mercadopublico.buyer"].search(
                    [("is_favorite", "=", True)]
                )
                for agency in favorite_agencies:
                    if not self._check_quota_available():
                        break
                    result = client.get_tenders_by_date_v1(
                        search_date_str, agency_code=agency.codigo
                    )
                    raw_records.extend(result.get("Listado", []))
            else:
                if not self._check_quota_available():
                    return {"nuevas": 0, "existentes": 0}
                result = client.get_tenders_by_date_v1(search_date_str)
                raw_records = result.get("Listado", []) if isinstance(result, dict) else []

            _logger.info("API v1 returned %d preliminary records.", len(raw_records))

            existing_codes = set(
                self.env["mercadopublico.tender"]
                .search([("process_type", "=", "licitacion")])
                .mapped("codigo")
            )
            processed_codes: set = set()

            for raw_tender in raw_records:
                code = raw_tender.get("CodigoExterno")
                if not code or code in processed_codes:
                    continue
                processed_codes.add(code)
                if code in existing_codes:
                    existing_count += 1
                    continue
                self.env["mercadopublico.tender"].create({
                    "name": raw_tender.get("Nombre", "Sin nombre"),
                    "codigo": code,
                    "process_type": "licitacion",
                    "buyer_name": raw_tender.get("NombreOrganismo"),
                    "estado": map_tender_status_v1(raw_tender.get("CodigoEstado")),
                    "state": "nuevo",
                    "filter_decision": "pendiente",
                })
                new_count += 1

            _logger.info("v1 sync complete. Created: %d, Skipped: %d.", new_count, existing_count)
            return {"nuevas": new_count, "existentes": existing_count}
        finally:
            self._release_sync_lock()
            if stats["success"] or stats["fail"]:
                comp = self.env.company.sudo()
                comp.write({
                    "mercadopublico_api_success": comp.mercadopublico_api_success + stats["success"],
                    "mercadopublico_api_fail": comp.mercadopublico_api_fail + stats["fail"],
                })
        raw_records: list = []
        agency_filter_mode = config.mercadopublico_keyword_organismo_favorito

        if agency_filter_mode == "excluyente":
            favorite_agencies = self.env["mercadopublico.buyer"].search(
                [("is_favorite", "=", True)]
            )
            for agency in favorite_agencies:
                if not self._check_quota_available():
                    break
                result = client.get_tenders_by_date_v1(
                    search_date_str, agency_code=agency.codigo
                )
                raw_records.extend(result.get("Listado", []))
        else:
            if not self._check_quota_available():
                return {"nuevas": 0, "existentes": 0}
            result = client.get_tenders_by_date_v1(search_date_str)
            raw_records = result.get("Listado", []) if isinstance(result, dict) else []

        _logger.info("API v1 returned %d preliminary records.", len(raw_records))

        existing_codes = set(
            self.env["mercadopublico.tender"]
            .search([("process_type", "=", "licitacion")])
            .mapped("codigo")
        )
        processed_codes: set = set()

        for raw_tender in raw_records:
            code = raw_tender.get("CodigoExterno")
            if not code or code in processed_codes:
                continue
            processed_codes.add(code)
            if code in existing_codes:
                existing_count += 1
                continue
            self.env["mercadopublico.tender"].create({
                "name": raw_tender.get("Nombre", "Sin nombre"),
                "codigo": code,
                "process_type": "licitacion",
                "buyer_name": raw_tender.get("NombreOrganismo"),
                "estado": map_tender_status_v1(raw_tender.get("CodigoEstado")),
                "state": "nuevo",
                "filter_decision": "pendiente",
            })
            new_count += 1

        _logger.info("v1 sync complete. Created: %d, Skipped: %d.", new_count, existing_count)
        return {"nuevas": new_count, "existentes": existing_count}

    @api.model
    def sync_quick_buys_v2(self) -> dict:
        """
        Downloads the v2 quick buy listing using the configured TTL window,
        applies in-memory pre-filters, and creates or updates records.

        Pre-filtering in memory (before DB writes) reduces unnecessary queries:
        - Strict agency filter: skips records not matching favorite agency names.
        - Region filter: skips records outside allowed region codes.

        State changes on existing records are detected and written without
        fetching the full detail payload, preserving API quota.

        Returns:
            dict: Counts with keys 'nuevas' (created) and 'existentes' (updated/skipped).
        """
        config = self._get_company_config()
        new_count, existing_count = 0, 0

        if not config.mercadopublico_sync_quick_buys:
            return {"nuevas": new_count, "existentes": existing_count}

        if not self._acquire_sync_lock():
            return {"nuevas": 0, "existentes": 0}

        stats = {"success": 0, "fail": 0}
        def track_quota(ok: bool):
            stats["success" if ok else "fail"] += 1

        try:
            ttl_min = config.mercadopublico_v2_ttl_minutes or 60

            # Nueva estrategia: Solo descargamos registros creados (publicados) recientemente.
            # Debido al bug de timezone de la API, compensamos la hora restando el offset de Chile.
            tz_chile = pytz.timezone("America/Santiago")
            now_utc = datetime.now(pytz.utc)
            now_chile = now_utc.astimezone(tz_chile)
            offset_seconds = now_chile.utcoffset().total_seconds()
            
            shifted_end_utc = now_utc + timedelta(seconds=offset_seconds)
            shifted_start_utc = shifted_end_utc - timedelta(minutes=ttl_min)

            published_from_str = shifted_start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            published_until_str = shifted_end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

            _logger.info(
                "Starting v2 quick buy sync (NEW STRATEGY): published_from=%s to %s (%d min configured + offset applied).",
                published_from_str,
                published_until_str,
                ttl_min,
            )

            client = self._get_api_client(quota_callback=track_quota)
            raw_records = client.get_quick_buys_v2(
                published_from=published_from_str,
                published_until=published_until_str
            )
            _logger.info("API v2 returned %d new records in the publication window.", len(raw_records))

            # Build in-memory pre-filter data once to avoid repeated ORM queries in the loop.
            agency_filter_mode = config.mercadopublico_keyword_organismo_favorito
            strict_agency_filter = config.mercadopublico_strict_buyer_mode
            favorite_agencies = self.env["mercadopublico.buyer"].search(
                [("is_favorite", "=", True)]
            )
            favorite_agency_names = [o.name.lower() for o in favorite_agencies if o.name]

            location_filter_mode = config.mercadopublico_location_mode
            allowed_region_codes: set = set()
            if location_filter_mode == "excluyente":
                for loc in config.mercadopublico_location_ids:
                    try:
                        if loc.tipo == "region" and loc.codigo_region_api:
                            allowed_region_codes.add(int(loc.codigo_region_api))
                        elif loc.tipo == "comuna" and loc.parent_id and loc.parent_id.codigo_region_api:
                            allowed_region_codes.add(int(loc.parent_id.codigo_region_api))
                    except (ValueError, TypeError):
                        pass

            tender_model = self.env["mercadopublico.tender"]
            processed_codes: set = set()

            for raw_quick_buy in raw_records:
                code = raw_quick_buy.get("codigo")
                if not code or code in processed_codes:
                    continue
                processed_codes.add(code)

                buyer_agency_name = (
                    raw_quick_buy.get("institucion", {}).get("organismo_comprador", "").strip()
                )

                # Pre-filter: strict favorite agency check on listing data (saves detail API calls).
                if agency_filter_mode == "excluyente" and strict_agency_filter and favorite_agency_names:
                    name_lower = buyer_agency_name.lower()
                    if not any(
                        fav in name_lower or name_lower in fav for fav in favorite_agency_names
                    ):
                        continue

                # Pre-filter: region code check on listing data.
                if location_filter_mode == "excluyente" and allowed_region_codes:
                    region_api = raw_quick_buy.get("institucion", {}).get("region")
                    if region_api is not None:
                        try:
                            if int(region_api) not in allowed_region_codes:
                                continue
                        except (ValueError, TypeError):
                            continue

                existing = tender_model.search(
                    [("codigo", "=", code), ("process_type", "=", "compra_agil")], limit=1
                )
                api_status = raw_quick_buy.get("estado", {}).get("codigo", "publicada")

                if existing:
                    existing_count += 1
                    if existing.estado != api_status:
                        _logger.info(
                            "Quick buy %s changed status: %s → %s.", code, existing.estado, api_status
                        )
                        existing.write({"estado": api_status})
                    continue

                tender_model.create({
                    "name": raw_quick_buy.get("nombre", "Sin nombre"),
                    "codigo": code,
                    "process_type": "compra_agil",
                    "buyer_name": buyer_agency_name,
                    "estado": api_status,
                    "state": "nuevo",
                    "filter_decision": "pendiente",
                })
                new_count += 1

            _logger.info("v2 sync complete. Created: %d, Skipped: %d.", new_count, existing_count)
            return {"nuevas": new_count, "existentes": existing_count}
        finally:
            self._release_sync_lock()
            if stats["success"] or stats["fail"]:
                comp = self.env.company.sudo()
                comp.write({
                    "mercadopublico_api_success": comp.mercadopublico_api_success + stats["success"],
                    "mercadopublico_api_fail": comp.mercadopublico_api_fail + stats["fail"],
                })
        raw_records = client.get_quick_buys_v2(
            published_from=published_from_str,
            published_until=published_until_str
        )
        _logger.info("API v2 returned %d new records in the publication window.", len(raw_records))

        # Build in-memory pre-filter data once to avoid repeated ORM queries in the loop.
        agency_filter_mode = config.mercadopublico_keyword_organismo_favorito
        strict_agency_filter = config.mercadopublico_strict_buyer_mode
        favorite_agencies = self.env["mercadopublico.buyer"].search(
            [("is_favorite", "=", True)]
        )
        favorite_agency_names = [o.name.lower() for o in favorite_agencies if o.name]

        location_filter_mode = config.mercadopublico_location_mode
        allowed_region_codes: set = set()
        if location_filter_mode == "excluyente":
            for loc in config.mercadopublico_location_ids:
                try:
                    if loc.tipo == "region" and loc.codigo_region_api:
                        allowed_region_codes.add(int(loc.codigo_region_api))
                    elif loc.tipo == "comuna" and loc.parent_id and loc.parent_id.codigo_region_api:
                        allowed_region_codes.add(int(loc.parent_id.codigo_region_api))
                except (ValueError, TypeError):
                    pass

        tender_model = self.env["mercadopublico.tender"]
        processed_codes: set = set()

        for raw_quick_buy in raw_records:
            code = raw_quick_buy.get("codigo")
            if not code or code in processed_codes:
                continue
            processed_codes.add(code)

            buyer_agency_name = (
                raw_quick_buy.get("institucion", {}).get("organismo_comprador", "").strip()
            )

            # Pre-filter: strict favorite agency check on listing data (saves detail API calls).
            if agency_filter_mode == "excluyente" and strict_agency_filter and favorite_agency_names:
                name_lower = buyer_agency_name.lower()
                if not any(
                    fav in name_lower or name_lower in fav for fav in favorite_agency_names
                ):
                    continue

            # Pre-filter: region code check on listing data.
            if location_filter_mode == "excluyente" and allowed_region_codes:
                region_api = raw_quick_buy.get("institucion", {}).get("region")
                if region_api is not None:
                    try:
                        if int(region_api) not in allowed_region_codes:
                            continue
                    except (ValueError, TypeError):
                        continue

            existing = tender_model.search(
                [("codigo", "=", code), ("process_type", "=", "compra_agil")], limit=1
            )
            api_status = raw_quick_buy.get("estado", {}).get("codigo", "publicada")

            if existing:
                existing_count += 1
                if existing.estado != api_status:
                    _logger.info(
                        "Quick buy %s changed status: %s → %s.", code, existing.estado, api_status
                    )
                    existing.write({"estado": api_status})
                continue

            tender_model.create({
                "name": raw_quick_buy.get("nombre", "Sin nombre"),
                "codigo": code,
                "process_type": "compra_agil",
                "buyer_name": buyer_agency_name,
                "estado": api_status,
                "state": "nuevo",
                "filter_decision": "pendiente",
            })
            new_count += 1

        _logger.info("v2 sync complete. Created: %d, Skipped: %d.", new_count, existing_count)
        return {"nuevas": new_count, "existentes": existing_count}

    @api.model
    def update_tracked_tenders_status(self):
        """
        Fetches the latest status from the API for tracked (apta) quick buys
        that are not yet in a terminal state, and updates them locally.
        """
        terminal_states = [
            "desierta", "adjudicada", "revocada", 
            "suspendida", "cancelada", "proveedor_seleccionado"
        ]
        
        tenders = self.env["mercadopublico.tender"].search([
            ("process_type", "=", "compra_agil"),
            ("filter_decision", "=", "apta"),
            ("estado", "not in", terminal_states)
        ])
        
        if not tenders:
            _logger.info("No active tracked quick buys to update.")
            return
            
        _logger.info("Updating status for %d tracked quick buys.", len(tenders))
        
        client = self._get_api_client()
        updated_count = 0
        
        for tender in tenders:
            detail = client.get_quick_buy_detail_v2(tender.codigo)
            if not detail:
                continue
                
            api_status = detail.get("estado", {}).get("codigo")
            if api_status and api_status != tender.estado:
                _logger.info(
                    "Tracked quick buy %s changed status: %s → %s.", 
                    tender.codigo, tender.estado, api_status
                )
                tender.write({"estado": api_status})
                updated_count += 1
                
        _logger.info("Status update complete. Updated %d records.", updated_count)

    @api.model
    def sync_buyers(self) -> None:
        """
        Downloads and persists the full list of registered buyer agencies.

        Skips agencies already present in the database (by code). Respects
        the quota check before making the API call.
        """
        if not self._check_quota_available():
            _logger.warning("Quota exhausted. Skipping buyer agency sync.")
            return

        client = self._get_api_client()
        agencies = client.get_buyer_agencies()

        existing_codes = set(
            self.env["mercadopublico.buyer"].search([]).mapped("codigo")
        )
        for agency in agencies:
            code = agency.get("CodigoEmpresa")
            if not code or code in existing_codes:
                continue
            self.env["mercadopublico.buyer"].create({
                "codigo": code,
                "name": agency.get("NombreEmpresa"),
            })

    # -------------------------------------------------------------------------
    # Analysis pipeline
    # -------------------------------------------------------------------------

    @api.model
    def process_pending_batch(self, limit: int = 50) -> int:
        """
        Fetches a batch of 'nuevo' records and runs them through the full
        scoring pipeline, persisting results to the database.

        Recovery step: records stuck in 'analizando' for more than 15 minutes
        (e.g. from an interrupted cron run) are reset to 'nuevo' before the
        batch is selected.

        Args:
            limit (int): Maximum number of records to process in this batch.

        Returns:
            int: Number of records successfully processed.
        """
        # Recover stale records from a previously interrupted batch.
        stale_threshold = fields.Datetime.now() - timedelta(minutes=15)
        stale_records = self.env["mercadopublico.tender"].search(
            [("state", "=", "analizando"), ("write_date", "<", stale_threshold)]
        )
        if stale_records:
            stale_records.write({"state": "nuevo"})

        pending_records = self.env["mercadopublico.tender"].search(
            [("state", "=", "nuevo")], limit=limit
        )
        if not pending_records:
            return 0

        _logger.info("Processing batch of %d pending records.", len(pending_records))
        pending_records.write({"state": "analizando"})

        config = self._get_company_config()
        active_keywords = config.mercadopublico_keyword_ids.filtered(
            lambda k: k.active
        )
        filter_category_ids: set = set(config.mercadopublico_category_ids.ids)

        # Merge in UNSPSC categories mapped to products/product categories.
        if "product.template" in self.env:
            product_cats = self.env["product.template"].search([]).mapped(
                "todas_mercadopublico_category_ids"
            )
            filter_category_ids.update(product_cats.ids)

        has_filters = bool(active_keywords) or bool(filter_category_ids)
        stats = {"success": 0, "fail": 0}
        def track_quota(ok: bool):
            stats["success" if ok else "fail"] += 1
        client = self._get_api_client(quota_callback=track_quota)
        processed_count = 0

        try:
            for record in pending_records:
                try:
                    api_payload = None
                    field_vals: dict = {}
                    items_to_create: list = []
                    extracted_category_codes: list = []
                    search_text = ""

                    if record.process_type == "licitacion":
                        if not self._check_quota_available():
                            _logger.warning("Quota exhausted mid-batch. Requeueing record %s.", record.codigo)
                            record.write({"state": "nuevo"})
                            break
                        api_payload = client.get_tender_detail_v1(record.codigo)
                        if api_payload:
                            field_vals = map_tender_fields_v1(api_payload)
                            search_text = (
                                f"{field_vals.get('name', '')} {field_vals.get('descripcion', '')}"
                            ).lower()
                            items_to_create, extracted_category_codes = extract_v1_items(api_payload)

                    else:  # compra_agil
                        if not self._check_quota_available():
                            _logger.warning("Quota exhausted mid-batch. Requeueing record %s.", record.codigo)
                            record.write({"state": "nuevo"})
                            break
                        api_payload = client.get_quick_buy_detail_v2(record.codigo)
                        if api_payload:
                            field_vals = map_quick_buy_fields_v2(api_payload)
                            search_text = (
                                f"{field_vals.get('name', '')} {field_vals.get('descripcion', '')}"
                            ).lower()
                            items_to_create, extracted_category_codes = extract_v2_items(api_payload)

                    if not api_payload:
                        _logger.warning(
                            "No detail data for %s. Requeueing.", record.codigo
                        )
                        record.write({"state": "nuevo"})
                        continue

                    # Resolve extracted category codes to ORM records.
                    matched_categories = self.env["mercadopublico.category"]
                    category_ids: list = []
                    if extracted_category_codes:
                        matched_categories = self.env["mercadopublico.category"].search(
                            [("codigo", "in", extracted_category_codes)]
                        )
                        category_ids = matched_categories.ids
                    if category_ids:
                        field_vals["category_ids"] = [(6, 0, category_ids)]

                    # Annotate each item with an individual match flag for UI display.
                    if items_to_create:
                        for idx, (_, _, item_vals) in enumerate(items_to_create):
                            item_text = f"{item_vals.get('name', '')} {item_vals.get('description', '')}".lower()
                            item_match = False

                            item_cat_code = item_vals.get("category_code", "")
                            if filter_category_ids and item_cat_code:
                                cat_record = matched_categories.filtered(
                                    lambda c, code=item_cat_code: c.codigo == code
                                )
                                if cat_record and cat_record.id in filter_category_ids:
                                    item_match = True

                            if not item_match:
                                from .services.scoring import find_matching_keyword
                                item_match = find_matching_keyword(item_text, active_keywords) is not None

                            items_to_create[idx][2]["is_match"] = item_match

                        field_vals["item_ids"] = [(5, 0, 0)] + items_to_create

                    # Evaluate location and agency conditions for the scoring call.
                    location_mode = config.mercadopublico_location_mode
                    location_match = False
                    if location_mode != "desactivado" and config.mercadopublico_location_ids:
                        buyer_commune = (field_vals.get("buyer_commune") or "").lower()
                        buyer_region = (field_vals.get("buyer_region") or "").lower()
                        location_match = any(
                            u.name.lower() in buyer_commune or u.name.lower() in buyer_region
                            for u in config.mercadopublico_location_ids
                        )

                    agency_mode = config.mercadopublico_keyword_organismo_favorito
                    agency_is_favorite = False
                    if agency_mode != "desactivado":
                        buyer_code = field_vals.get("buyer_code", "")
                        agency = self.env["mercadopublico.buyer"].search(
                            [("codigo", "=", buyer_code)], limit=1
                        )
                        agency_is_favorite = agency.is_favorite if agency else False

                    scoring: ScoringResult = score_tender(
                        search_text=search_text,
                        category_ids=category_ids,
                        filter_category_ids=filter_category_ids,
                        active_keywords=active_keywords,
                        location_mode=location_mode,
                        location_match=location_match,
                        agency_mode=agency_mode,
                        agency_is_favorite=agency_is_favorite,
                    )

                    field_vals["state"] = "analizado"
                    field_vals["filter_decision"] = "apta" if scoring.is_match else "no_apta"
                    field_vals["match_summary"] = scoring.reason
                    field_vals["rating"] = str(min(scoring.score, 3))

                    if scoring.is_match:
                        stage = self.env.ref(
                            "mercadopublico_odoo_integration.etapa_en_espera",
                            raise_if_not_found=False,
                        )
                        if stage:
                            field_vals["stage_id"] = stage.id
                    else:
                        stage = self.env.ref(
                            "mercadopublico_odoo_integration.etapa_descartada",
                            raise_if_not_found=False,
                        )
                        if stage:
                            field_vals["stage_id"] = stage.id

                    record.write(field_vals)

                    if scoring.is_match:
                        self._notify_match(record)

                    processed_count += 1
                    # Brief pause to avoid API burst limit on consecutive detail calls.
                    time.sleep(0.3)

                except Exception as e:
                    _logger.error("Error processing record %s: %s", record.codigo, e)
                    record.write({"state": "nuevo"})
        finally:
            if stats["success"] or stats["fail"]:
                comp = self.env.company.sudo()
                comp.write({
                    "mercadopublico_api_success": comp.mercadopublico_api_success + stats["success"],
                    "mercadopublico_api_fail": comp.mercadopublico_api_fail + stats["fail"],
                })

        return processed_count

    def _notify_match(self, record) -> None:
        """
        Posts an HTML notification to the configured Discuss channel when a
        tender is classified as a match.

        Constructs a deep-link URL to the Odoo record using the window action
        reference, falling back to a generic model URL if the action is missing.

        Args:
            record: A ``mercadopublico.tender`` record in 'apta' state.
        """
        config = self._get_company_config()
        channel = config.mercadopublico_discuss_channel_id or self.env.ref(
            "mercadopublico_odoo_integration.channel_mercadopublico",
            raise_if_not_found=False,
        )
        if not channel:
            return

        odoobot = self.env.ref("base.partner_root", raise_if_not_found=False)
        author_id = odoobot.id if odoobot else self.env.user.partner_id.id

        amount_fmt = "{:,.0f}".format(record.estimated_amount).replace(",", ".")
        process_type_label = dict(
            self.env["mercadopublico.tender"]._fields["process_type"].selection
        ).get(record.process_type)

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        action = self.env.ref(
            "mercadopublico_odoo_integration.action_mercadopublico_tender",
            raise_if_not_found=False,
        )
        action_id = action.id if action else ""
        odoo_url = (
            f"{base_url}/odoo/action-{action_id}/{record.id}"
            if action_id
            else f"{base_url}/odoo/mercadopublico.tender/{record.id}"
        )

        msg_html = f"""
            <div style="padding: 10px; border-left: 4px solid #714B67; margin-bottom: 10px;">
                <ul style="list-style-type: none; padding-left: 0; margin-bottom: 15px;">
                    <li style="margin-bottom: 4px;"><b>Tipo:</b> {process_type_label}</li>
                    <li style="margin-bottom: 4px;"><b>Nombre:</b> {record.name}</li>
                    <li style="margin-bottom: 4px;"><b>Organismo:</b> {record.buyer_name}</li>
                    <li style="margin-bottom: 4px;"><b>Monto Estimado:</b> {record.moneda} {amount_fmt}</li>
                    <li style="margin-bottom: 4px;"><b>Motivo:</b> <span style="color: #28a745;">{record.match_summary}</span></li>
                </ul>
                <div style="display: flex; flex-direction: column; gap: 8px; max-width: 250px;">
                    <a href="{odoo_url}" target="_blank" style="display: block; text-decoration: none; padding: 6px 12px; background-color: #714B67; color: white; border-radius: 4px; text-align: center;">🔗 Ver en Odoo</a>
                    <a href="{record.source_url}" target="_blank" style="display: block; text-decoration: none; padding: 6px 12px; background-color: #007bff; color: white; border-radius: 4px; text-align: center;">🌐 Ver en Mercado Público</a>
                </div>
            </div>
        """
        channel.with_context(mail_create_nosubscribe=True).message_post(
            body=Markup(msg_html),
            message_type="comment",
            author_id=author_id,
        )

    # -------------------------------------------------------------------------
    # Cron entrypoints
    # -------------------------------------------------------------------------

    @api.model
    def cron_sync_tenders(self) -> None:
        """Cron entrypoint: imports v1 tenders."""
        self.sync_tenders_v1()

    @api.model
    def cron_sync_quick_buys(self) -> None:
        """Cron entrypoint: imports v2 quick buys."""
        self.sync_quick_buys_v2()

    @api.model
    def cron_analyze_tenders(self) -> None:
        """Cron entrypoint: processes a full analysis batch without importing new records."""
        if self.env.company.mercadopublico_is_syncing:
            _logger.info("Discovery sync in progress. Skipping analysis cron execution.")
            return
        self.process_pending_batch(limit=50)
