"""
Extension of crm.lead with Mercado Público tender linkage fields.

When a tender is converted to an opportunity, these fields are populated
automatically by ``MercadoPublicoTender.action_convert_to_opportunity``.
"""
from odoo import _, api, fields, models


class CrmLead(models.Model):
    """Extends crm.lead with fields linking the opportunity to its source tender."""

    _inherit = "crm.lead"

    mercadopublico_id = fields.Many2one(
        "mercadopublico.tender",
        string="Licitación de Mercado Público",
        ondelete="set null",
        help="Licitación de Mercado Público relacionada con esta oportunidad.",
    )
    mercadopublico_code = fields.Char(
        string="Código Licitación",
        readonly=True,
    )
    mercadopublico_closing_date = fields.Datetime(
        string="Fecha Cierre Licitación",
        readonly=True,
    )
    is_mercadopublico = fields.Boolean(
        string="Es de Mercado Público",
        compute="_compute_is_mercadopublico",
        store=True,
    )

    @api.depends("mercadopublico_id")
    def _compute_is_mercadopublico(self):
        """True when the opportunity was created from a Mercado Público tender."""
        for lead in self:
            lead.is_mercadopublico = bool(lead.mercadopublico_id)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Creates CRM leads and performs post-creation enrichment for MP-sourced records.

        For each new lead linked to a tender:
        - Sets ``date_deadline`` from the tender closing date if not already provided.
        - Posts an internal note with a hyperlink to the source tender record.

        Args:
            vals_list (list[dict]): List of field value dictionaries.

        Returns:
            recordset: The newly created crm.lead records.
        """
        leads = super().create(vals_list)
        for lead in leads:
            if not lead.mercadopublico_id:
                continue
            if not lead.date_deadline and lead.mercadopublico_closing_date:
                lead.date_deadline = lead.mercadopublico_closing_date
            url = lead.mercadopublico_id.source_url
            if url:
                lead.message_post(
                    body=_(
                        "Esta oportunidad fue creada desde la licitación de Mercado Público: "
                        "<a href='%s' target='_blank'>%s</a>"
                    ) % (url, lead.mercadopublico_code or lead.mercadopublico_id.codigo),
                    subject=_("Creado desde Mercado Público"),
                )
        return leads

    def action_view_mercadopublico_tender(self):
        """
        Opens the source tender record in the current window.

        Returns:
            dict | None: act_window action for the linked tender, or None
                         if no tender is linked.
        """
        self.ensure_one()
        if not self.mercadopublico_id:
            return None
        return {
            "type": "ir.actions.act_window",
            "res_model": "mercadopublico.tender",
            "res_id": self.mercadopublico_id.id,
            "view_mode": "form",
            "target": "current",
        }