"""
TransientModel that proxies Mercado Público configuration fields for the
Odoo Settings UI (res.config.settings).

All fields are ``related`` to their canonical definitions on ``res.company``.
The ``set_values`` override additionally schedules the import cron job to the
user-defined hour, converting from the company's local timezone to UTC.
"""
import logging
from datetime import datetime, timedelta

import pytz

from odoo import fields, models

from .services.scoring import FUZZY_AVAILABLE

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """Settings form proxy for Mercado Público integration configuration."""

    _inherit = "res.config.settings"

    # API credentials
    mercadopublico_api_ticket = fields.Char(
        related="company_id.mercadopublico_api_ticket", readonly=False
    )
    mercadopublico_search_days_backward = fields.Integer(
        related="company_id.mercadopublico_search_days_backward", readonly=False
    )

    # Sync toggles
    mercadopublico_sync_tenders = fields.Boolean(
        related="company_id.mercadopublico_sync_tenders", readonly=False
    )
    mercadopublico_sync_quick_buys = fields.Boolean(
        related="company_id.mercadopublico_sync_quick_buys", readonly=False
    )

    # API quota (read/write for limits, read-only for counters)
    mercadopublico_api_limit = fields.Integer(
        related="company_id.mercadopublico_api_limit", readonly=False
    )
    mercadopublico_api_realizados = fields.Integer(
        related="company_id.mercadopublico_api_realizados", readonly=True
    )
    mercadopublico_api_success = fields.Integer(
        related="company_id.mercadopublico_api_success", readonly=True
    )
    mercadopublico_api_fail = fields.Integer(
        related="company_id.mercadopublico_api_fail", readonly=True
    )
    mercadopublico_api_reset = fields.Datetime(
        related="company_id.mercadopublico_api_reset", readonly=True
    )
    mercadopublico_cron_analysis_minutes = fields.Integer(
        related="company_id.mercadopublico_cron_analysis_minutes", readonly=False
    )
    mercadopublico_v2_ttl_minutes = fields.Integer(
        related="company_id.mercadopublico_v2_ttl_minutes", readonly=False
    )
    mercadopublico_status_update_interval_hours = fields.Integer(
        related="company_id.mercadopublico_status_update_interval_hours", readonly=False
    )

    # Notifications
    mercadopublico_discuss_channel_id = fields.Many2one(
        "discuss.channel",
        related="company_id.mercadopublico_discuss_channel_id",
        readonly=False,
    )

    # Agency filter
    mercadopublico_keyword_organismo_favorito = fields.Selection(
        related="company_id.mercadopublico_keyword_organismo_favorito", readonly=False
    )
    mercadopublico_strict_buyer_mode = fields.Boolean(
        related="company_id.mercadopublico_strict_buyer_mode", readonly=False
    )

    # Location filter
    mercadopublico_location_mode = fields.Selection(
        related="company_id.mercadopublico_location_mode", readonly=False
    )
    mercadopublico_location_ids = fields.Many2many(
        related="company_id.mercadopublico_location_ids", readonly=False
    )

    # Keyword and category filters
    mercadopublico_category_ids = fields.Many2many(
        related="company_id.mercadopublico_category_ids", readonly=False
    )
    mercadopublico_keyword_ids = fields.Many2many(
        related="company_id.mercadopublico_keyword_ids", readonly=False
    )
    mercadopublico_auto_import_tags = fields.Boolean(
        related="company_id.mercadopublico_auto_import_tags", readonly=False
    )

    # CRM defaults
    mercadopublico_crm_team_id = fields.Many2one(
        related="company_id.mercadopublico_crm_team_id", readonly=False
    )
    mercadopublico_crm_user_id = fields.Many2one(
        related="company_id.mercadopublico_crm_user_id", readonly=False
    )

    # Scheduling and retention
    mercadopublico_cron_hour = fields.Float(
        related="company_id.mercadopublico_cron_hour", readonly=False
    )
    mercadopublico_retention_days_rejected = fields.Integer(
        related="company_id.mercadopublico_retention_days_rejected", readonly=False
    )

    # Dependency status indicator (display-only, computed from import check)
    mercadopublico_status_libraries = fields.Selection(
        [("ok", "Instaladas"), ("missing", "Faltan")],
        default=lambda self: "ok" if FUZZY_AVAILABLE else "missing",
    )

    def set_values(self):
        """
        Saves settings and reschedules the tender import cron to the configured hour.

        Converts the user-defined hour (stored as a float on res.company) from
        the current user's timezone to UTC before writing the cron nextcall.
        """
        super().set_values()

        cron = self.env.ref(
            "mercadopublico_odoo_integration.ir_cron_mercadopublico_import_tenders",
            raise_if_not_found=False,
        )
        if not cron:
            return

        hour = int(self.mercadopublico_cron_hour)
        minute = int((self.mercadopublico_cron_hour - hour) * 60)

        tz_name = self.env.user.tz or "America/Santiago"
        user_tz = pytz.timezone(tz_name)
        now_user = datetime.now(pytz.utc).astimezone(user_tz)

        next_call = now_user.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_call <= now_user:
            next_call += timedelta(days=1)

        next_call_utc = next_call.astimezone(pytz.utc).replace(tzinfo=None)
        cron.sudo().write({"nextcall": next_call_utc})

        cron_analisis = self.env.ref(
            "mercadopublico_odoo_integration.ir_cron_mercadopublico_analyze_tenders",
            raise_if_not_found=False,
        )
        if cron_analisis and self.mercadopublico_cron_analysis_minutes:
            cron_analisis.sudo().write({
                "interval_number": self.mercadopublico_cron_analysis_minutes,
                "interval_type": "minutes",
            })

        cron_status = self.env.ref(
            "mercadopublico_odoo_integration.ir_cron_mercadopublico_update_status",
            raise_if_not_found=False,
        )
        if cron_status and self.mercadopublico_status_update_interval_hours:
            cron_status.sudo().write({
                "interval_number": self.mercadopublico_status_update_interval_hours,
                "interval_type": "hours",
            })

    def action_get_api_key(self):
        """Opens the ChileCompra API key registration page in a new tab."""
        return {
            "type": "ir.actions.act_url",
            "url": "https://www.chilecompra.cl/api/",
            "target": "new",
        }

    def action_reset_api_quota(self):
        """
        Resets the daily API counter to zero and clears any active quota block.

        Returns:
            dict: A client notification action confirming the reset.
        """
        self.company_id.mercadopublico_api_realizados = 0
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Cuota Reiniciada",
                "message": "Se ha puesto a cero el contador diario y se ha desbloqueado la API.",
                "type": "success",
                "sticky": False,
            },
        }
