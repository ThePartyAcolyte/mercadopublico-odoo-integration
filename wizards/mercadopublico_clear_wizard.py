"""
Wizard for manually bulk-deleting tender and quick buy records.

Provides configurable filters (date range, decision filter, CRM linkage)
to allow selective data retention cleanup beyond the automatic cron schedule.
"""
from datetime import timedelta

from odoo import _, fields, models


class MercadoPublicoClearWizard(models.TransientModel):
    """Transient wizard for selective bulk deletion of tender records."""

    _name = "mercadopublico.clear.wizard"
    _description = "Asistente de Limpieza de Licitaciones"

    days = fields.Integer("Días hacia atrás", default=30, required=True)
    only_unsuitable = fields.Boolean("Solo Licitaciones No Aptas", default=True)
    only_without_opportunity = fields.Boolean("Solo sin Oportunidad CRM", default=True)

    def action_clear(self):
        """
        Deletes tender records matching the configured criteria.

        Returns:
            dict: A success notification client action with the deletion count.
        """
        self.ensure_one()
        cutoff_date = fields.Datetime.now() - timedelta(days=self.days)
        domain = [("create_date", "<", cutoff_date)]

        if self.only_unsuitable:
            domain.append(("filter_decision", "=", "no_apta"))
        if self.only_without_opportunity:
            domain.append(("opportunity_id", "=", False))

        records = self.env["mercadopublico.tender"].search(domain)
        count = len(records)
        records.unlink()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Limpieza Completada"),
                "message": _(
                    "Se han eliminado %d registros (Licitaciones y Compras Ágiles)."
                ) % count,
                "type": "success",
                "sticky": False,
            },
        }
