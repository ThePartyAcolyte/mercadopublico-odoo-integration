"""
HTTP client for the Mercado Público (ChileCompra) API.

This module has no Odoo ORM dependencies. All classes and functions are pure
Python and can be tested without instantiating a database environment.
Supports API v1 (Licitaciones Públicas) and v2 (Compra Ágil).
"""
import logging
import time

import requests

_logger = logging.getLogger(__name__)

_V1_BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico"
_V2_BASE_URL = "https://api2.mercadopublico.cl/v2"

# Maximum number of pages to retrieve from the v2 paginated endpoint.
# Prevents infinite loops when the API reports an unexpectedly large total_pages.
_V2_PAGE_HARD_LIMIT = 50

# Pause between consecutive v2 paginated requests to respect the burst rate limit.
_REQUEST_THROTTLE_SECONDS = 0.5


class ChileCompraApiClient:
    """
    Stateless HTTP client for the Mercado Público (ChileCompra) API.

    Handles authentication and static retries on failures.

    Args:
        api_token (str): API authentication token (ticket) for all requests.
    """

    def __init__(self, api_token: str, quota_callback=None):
        self._token = api_token
        self._quota_callback = quota_callback

    # -------------------------------------------------------------------------
    # API v1 — Licitaciones Públicas
    # -------------------------------------------------------------------------

    def get_tenders_by_date_v1(
        self, date_str: str, agency_code: str | None = None
    ) -> dict:
        """
        Fetches published tenders from the v1 API for a given date.

        Args:
            date_str (str): Date in 'DDMMYYYY' format.
            agency_code (str | None): Optional buyer agency code to restrict results.

        Returns:
            dict: API response containing a 'Listado' key. Returns
                  {'Listado': []} on failure.
        """
        url = f"{_V1_BASE_URL}/licitaciones.json"
        params = {"fecha": date_str, "estado": "publicada", "ticket": self._token}
        if agency_code:
            params["CodigoOrganismo"] = agency_code
        try:
            safe_params = params.copy()
            if "ticket" in safe_params:
                safe_params["ticket"] = "***"
            _logger.info("Fetching v1 tenders: URL=%s, params=%s", url, safe_params)
            response = requests.get(url, params=params, timeout=20)
            self._report_request(response.status_code == 200)
            if response.status_code == 429:
                _logger.warning("v1 tenders: 429 Too Many Requests")
                return {"Listado": []}
            response.raise_for_status()
            data = response.json()
            # If the API returns a 'mensaje' indicating failure (sometimes they do 200 OK with error messages inside)
            if "Listado" not in data:
                _logger.error("v1 tenders returned unexpected format: %s", data)
            return data
        except Exception as e:
            _logger.error("Error fetching v1 tenders for date '%s': %s (Response: %s)", date_str, e, response.text if 'response' in locals() else 'None')
            return {"Listado": []}

    def get_tender_detail_v1(
        self, code: str, max_retries: int = 1
    ) -> dict | None:
        """
        Fetches the full detail record for a single v1 tender.

        Args:
            code (str): Tender external code (CodigoExterno).
            max_retries (int): Number of additional attempts after the first. Defaults to 1.

        Returns:
            dict | None: Tender detail dict, or None if the record is
                         unavailable or an error occurred.
        """
        url = f"{_V1_BASE_URL}/licitaciones.json"
        params = {"codigo": code, "ticket": self._token}
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    time.sleep(3)
                response = requests.get(url, params=params, timeout=15)
                self._report_request(response.status_code == 200)
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt == max_retries:
                        return None
                    continue
                response.raise_for_status()
                data = response.json()
                if not data or "Listado" not in data or not data["Listado"]:
                    return None
                return data["Listado"][0]
            except Exception as e:
                _logger.warning(
                    "Error fetching v1 tender '%s' (attempt %d): %s", code, attempt, e
                )
        return None

    # -------------------------------------------------------------------------
    # API v2 — Compra Ágil
    # -------------------------------------------------------------------------

    def get_quick_buys_v2(
        self,
        published_from: str | None = None,
        published_until: str | None = None,
    ) -> list:
        """
        Fetches all published quick buys (Compra Ágil) from the v2 API.

        Paginates automatically until all results are retrieved or the hard
        page limit (_V2_PAGE_HARD_LIMIT) is reached to prevent runaway loops.

        Args:
            published_from (str | None): ISO date string for the window start.
            published_until (str | None): ISO date string for the window end.

        Returns:
            list: The combined list of items from all retrieved pages.
        """
        url = f"{_V2_BASE_URL}/compra-agil"
        headers = {"ticket": self._token}
        params: dict = {"tamano_pagina": 50, "numero_pagina": 1}

        if published_from:
            params["publicado_desde"] = published_from
        if published_until:
            params["publicado_hasta"] = published_until

        all_items: list = []
        try:
            while True:
                # Implementar reintentos en caso de Timeouts o Errores de Servidor (500, 502, 503, 504)
                max_retries = 3
                for attempt in range(max_retries + 1):
                    try:
                        if attempt > 0:
                            time.sleep(3)
                            _logger.info("Retrying v2 quick buys page %d (attempt %d/%d)", params.get("numero_pagina", 1), attempt, max_retries)
                        
                        _logger.info("Fetching v2 quick buys: URL=%s, params=%s", url, params)
                        response = requests.get(url, headers=headers, params=params, timeout=60)
                        self._report_request(response.status_code == 200)
                        
                        if response.status_code in (500, 502, 503, 504):
                            if attempt == max_retries:
                                response.raise_for_status() # Trigger exception to abort if we exhausted retries
                            continue # Try again
                            
                        if response.status_code == 429:
                            _logger.warning("v2 quick buys: 429 Too Many Requests")
                            break # We break the attempt loop, but below we also need to break the while True loop. Wait, raising an exception is easier to abort the outer loop.
                        
                        response.raise_for_status()
                        break # If we get here, the request was successful (200), break the retry loop
                        
                    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                        if attempt == max_retries:
                            raise e
                        continue
                
                if response is not None and response.status_code == 429:
                    break

                data = response.json()
                if data.get("success") != "OK":
                    _logger.error("v2 quick buys failed: %s", data)
                    break

                # Throttle between paginated requests to respect burst limits.
                time.sleep(_REQUEST_THROTTLE_SECONDS)

                payload = data.get("payload", {})
                items = payload.get("items", [])
                all_items.extend(items)
                
                _logger.info("v2 quick buys: received %d items in this page.", len(items))

                pagination = payload.get("paginacion", {})
                current_page = pagination.get("numero_pagina", 1)
                total_pages = pagination.get("total_paginas", 1)

                if current_page >= total_pages or current_page >= _V2_PAGE_HARD_LIMIT:
                    if current_page >= _V2_PAGE_HARD_LIMIT and current_page < total_pages:
                        _logger.warning(
                            "Hard page limit (%d) reached for v2 quick buys. "
                            "Results may be incomplete.",
                            _V2_PAGE_HARD_LIMIT,
                        )
                    break
                params["numero_pagina"] += 1
        except Exception as e:
            resp_text = response.text if response is not None and hasattr(response, 'text') else 'None'
            _logger.error("Error fetching v2 quick buys: %s (Response: %s)", e, resp_text)
        return all_items

    def get_quick_buy_detail_v2(
        self, code: str, max_retries: int = 1
    ) -> dict | None:
        """
        Fetches the full payload for a single v2 quick buy record.

        Args:
            code (str): Quick buy code.
            max_retries (int): Number of additional attempts after the first. Defaults to 1.

        Returns:
            dict | None: Payload dict, or None on failure.
        """
        url = f"{_V2_BASE_URL}/compra-agil/{code}"
        headers = {"ticket": self._token}
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    time.sleep(3)
                response = requests.get(url, headers=headers, timeout=15)
                self._report_request(response.status_code == 200)
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt == max_retries:
                        return None
                    continue
                response.raise_for_status()
                data = response.json()
                if data.get("success") != "OK":
                    return None
                time.sleep(_REQUEST_THROTTLE_SECONDS)
                return data.get("payload")
            except Exception as e:
                _logger.warning(
                    "Error fetching v2 quick buy '%s' (attempt %d): %s",
                    code,
                    attempt,
                    e,
                )
        return None

    # -------------------------------------------------------------------------
    # Organismos
    # -------------------------------------------------------------------------

    def get_buyer_agencies(self) -> list:
        """
        Fetches the full list of registered buyer agencies (organismos compradores).

        Returns:
            list: The list of agency dicts from 'listaEmpresas'.
        """
        url = "https://api.mercadopublico.cl/servicios/v1/Publico/Empresas/BuscarComprador"
        try:
            response = requests.get(url, params={"ticket": self._token}, timeout=30)
            self._report_request(response.status_code == 200)
            if response.status_code == 429:
                return []
            response.raise_for_status()
            data = response.json()
            return data.get("listaEmpresas", [])
        except Exception as e:
            _logger.error("Error fetching buyer agencies: %s", e)
            return []

    def _report_request(self, success: bool):
        if self._quota_callback:
            try:
                self._quota_callback(success)
            except Exception as e:
                _logger.error("Error in quota callback: %s", e)
