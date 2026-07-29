"""
Main data model for Mercado Público tenders and quick buys.

A single model represents both process types (licitacion and compra_agil) to
avoid schema duplication, differentiated by the ``process_type`` selection field.
Integrates with the Odoo Kanban pipeline via ``mercadopublico.stage`` stages
and with the CRM module via ``opportunity_id``.
"""
from datetime import timedelta

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MercadoPublicoTender(models.Model):
    """
    Represents a public tender (licitación) or quick buy (compra ágil) record
    fetched from the Mercado Público API.

    Records are created in state 'nuevo' by the sync jobs and transition to
    'analizado' after the scoring pipeline runs. Relevant records can be
    converted into CRM opportunities via ``action_convert_to_opportunity``.
    """

    _name = "mercadopublico.tender"
    _description = "Licitación / Compra Ágil de Mercado Público"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha_publicacion desc"

    # -------------------------------------------------------------------------
    # Core identification fields
    # -------------------------------------------------------------------------

    name = fields.Char("Nombre", required=True, tracking=True)
    codigo = fields.Char("Código", required=True, tracking=True)
    descripcion = fields.Text("Descripción", tracking=True)

    process_type = fields.Selection(
        [
            ("licitacion", "Licitación Pública (v1)"),
            ("compra_agil", "Compra Ágil (v2)"),
        ],
        string="Tipo de Proceso",
        default="licitacion",
        required=True,
        tracking=True,
    )
    estado = fields.Selection(
        [
            ("publicada", "Publicada"),
            ("cerrada", "Cerrada"),
            ("desierta", "Desierta"),
            ("adjudicada", "Adjudicada"),
            ("revocada", "Revocada"),
            ("suspendida", "Suspendida"),
            ("proveedor_seleccionado", "Proveedor Seleccionado (CA)"),
            ("cancelada", "Cancelada"),
        ],
        string="Estado",
        tracking=True,
    )

    # -------------------------------------------------------------------------
    # Dates
    # -------------------------------------------------------------------------

    fecha_publicacion = fields.Datetime("Fecha Publicación", tracking=True)
    fecha_cierre = fields.Datetime("Fecha Cierre", tracking=True)
    fecha_adjudicacion = fields.Datetime("Fecha Adjudicación", tracking=True)

    # -------------------------------------------------------------------------
    # Buyer / agency information
    # -------------------------------------------------------------------------

    buyer_code = fields.Char("Código Organismo", tracking=True)
    buyer_name = fields.Char("Nombre Organismo", tracking=True)
    buyer_commune = fields.Char("Comuna", tracking=True)
    buyer_region = fields.Char("Región", tracking=True)

    buyer_id = fields.Many2one(
        "mercadopublico.buyer",
        string="Organismo",
        compute="_compute_buyer_id",
        store=True,
    )
    is_favorite_agency = fields.Boolean(
        related="buyer_id.is_favorite",
        string="Organismo Favorito",
        readonly=False,
    )

    # -------------------------------------------------------------------------
    # Financial and classification details
    # -------------------------------------------------------------------------

    moneda = fields.Char("Moneda", tracking=True)
    estimated_amount = fields.Float("Monto Estimado", tracking=True)
    source_url = fields.Char("URL Mercado Público", tracking=True)
    tipo_licitacion = fields.Char("Tipo Licitación", tracking=True)
    etapas = fields.Integer("Etapas", tracking=True)
    etapas_estado = fields.Char("Estado de Etapas", readonly=True, tracking=True)
    requires_toma_razon = fields.Boolean(
        "Requiere Toma de Razón", readonly=True, tracking=True
    )
    funding_source = fields.Char(
        "Fuente Financiamiento", readonly=True, tracking=True
    )

    # -------------------------------------------------------------------------
    # UNSPSC category and item classification
    # -------------------------------------------------------------------------

    category_ids = fields.Many2many(
        "mercadopublico.category", string="Categorías UNSPSC", tracking=True
    )
    item_ids = fields.One2many(
        "mercadopublico.tender.item", "tender_id", string="Productos/Ítems"
    )
    match_summary = fields.Text("Palabras clave encontradas")
    rating = fields.Selection(
        [("0", "0"), ("1", "1"), ("2", "2"), ("3", "3")],
        string="Relevancia",
        default="0",
        tracking=True,
    )

    # -------------------------------------------------------------------------
    # Processing pipeline state
    # -------------------------------------------------------------------------

    state = fields.Selection(
        [
            ("nuevo", "Nuevo"),
            ("analizando", "Analizando"),
            ("analizado", "Analizado"),
        ],
        string="Estado de Procesamiento",
        default="nuevo",
        index=True,
        tracking=True,
    )
    filter_decision = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("apta", "Apta"),
            ("no_apta", "No Apta"),
        ],
        string="Decisión de Filtro",
        default="pendiente",
        index=True,
        tracking=True,
    )
    stage_id = fields.Many2one(
        "mercadopublico.stage",
        string="Etapa",
        tracking=True,
        group_expand="_read_group_stage_ids",
    )

    # -------------------------------------------------------------------------
    # CRM linkage and tracking
    # -------------------------------------------------------------------------

    discard_reason = fields.Text("Motivo de descarte", tracking=True)
    opportunity_id = fields.Many2one("crm.lead", "Oportunidad", tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        tracking=True,
    )

    _codigo_uniq = models.Constraint(
        "unique(codigo, company_id)",
        "El código del proceso debe ser único por compañía.",
    )

    # -------------------------------------------------------------------------
    # Computed fields
    # -------------------------------------------------------------------------

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Returns all stages regardless of domain to keep Kanban columns always visible."""
        return stages.search([])

    @api.depends("buyer_code")
    def _compute_buyer_id(self):
        """Resolves the buyer agency code to its corresponding organismo record."""
        for record in self:
            if record.buyer_code:
                organismo = self.env["mercadopublico.buyer"].search(
                    [("codigo", "=", record.buyer_code)], limit=1
                )
                record.buyer_id = organismo.id
            else:
                record.buyer_id = False

    # -------------------------------------------------------------------------
    # Static helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_url(codigo: str, process_type: str) -> str:
        """
        Constructs the public Mercado Público URL for a given record.

        Args:
            codigo (str): Tender or quick buy external code.
            process_type (str): 'licitacion' or 'compra_agil'.

        Returns:
            str: Full URL to the record on www.mercadopublico.cl.
        """
        if process_type == "licitacion":
            return f"https://www.mercadopublico.cl/fichaLicitacion.html?idLicitacion={codigo}"
        return f"https://www.mercadopublico.cl/Home/FichaCompraAgil/{codigo}"

    # -------------------------------------------------------------------------
    # User actions
    # -------------------------------------------------------------------------

    def action_toggle_organismo_favorito(self):
        """
        Toggles the favorite flag for the buyer agency linked to this record.

        Creates the agency record if it does not yet exist in the database.
        """
        self.ensure_one()
        if not self.buyer_code:
            return
        organismo = self.env["mercadopublico.buyer"].search(
            [("codigo", "=", self.buyer_code)], limit=1
        )
        if not organismo:
            self.env["mercadopublico.buyer"].create({
                "name": self.buyer_name,
                "codigo": self.buyer_code,
                "is_favorite": True,
            })
        else:
            organismo.is_favorite = not organismo.is_favorite
        return True

    def action_discard(self):
        """Opens the feedback wizard in 'no_apta' mode to discard the record."""
        return {
            "name": _("Feedback de Licitación"),
            "type": "ir.actions.act_window",
            "res_model": "mercadopublico.tender.discard.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_tender_id": self.id,
                "default_action_type": "no_apta",
            },
        }

    def action_mark_as_suitable(self):
        """Opens the feedback wizard in 'apta' mode to mark the record as relevant."""
        return {
            "name": _("Feedback de Licitación"),
            "type": "ir.actions.act_window",
            "res_model": "mercadopublico.tender.discard.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_tender_id": self.id,
                "default_action_type": "apta",
            },
        }

    def action_convert_to_opportunity(self):
        """
        Converts this record into a CRM opportunity.

        If an opportunity already exists, navigates to it directly. Otherwise,
        creates a new ``crm.lead`` record with all relevant fields pre-filled
        and links it to this tender record.

        Returns:
            dict: An act_window action opening the CRM lead form.
        """
        self.ensure_one()
        stage_converted = self.env.ref(
            "mercadopublico_odoo_integration.etapa_convertida", raise_if_not_found=False
        )
        if self.opportunity_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "crm.lead",
                "res_id": self.opportunity_id.id,
                "view_mode": "form",
                "target": "current",
            }

        process_type_label = dict(
            self._fields["process_type"].selection
        ).get(self.process_type)
        opportunity_vals = {
            "name": f"{process_type_label}: {self.name}",
            "description": self.descripcion,
            "type": "opportunity",
            "partner_name": self.buyer_name,
            "city": self.buyer_commune,
            "mercadopublico_id": self.id,
            "mercadopublico_code": self.codigo,
            "mercadopublico_closing_date": self.fecha_cierre,
            "is_mercadopublico": True,
        }

        company = self.env.company
        if company.mercadopublico_crm_team_id:
            opportunity_vals["team_id"] = company.mercadopublico_crm_team_id.id
        if company.mercadopublico_crm_user_id:
            opportunity_vals["user_id"] = company.mercadopublico_crm_user_id.id

        opportunity = self.env["crm.lead"].create(opportunity_vals)
        write_vals = {"opportunity_id": opportunity.id}
        if stage_converted:
            write_vals["stage_id"] = stage_converted.id
        self.write(write_vals)

        return {
            "type": "ir.actions.act_window",
            "res_model": "crm.lead",
            "res_id": opportunity.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_mercadopublico(self):
        """
        Opens the Mercado Público website record in a new browser tab.

        Builds the URL on demand if it was not set during import.
        """
        self.ensure_one()
        if not self.source_url:
            self.source_url = self._build_url(self.codigo, self.process_type)
        return {"type": "ir.actions.act_url", "url": self.source_url, "target": "new"}

    # -------------------------------------------------------------------------
    # ORM overrides
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Ensures company_id and source_url are set on every new record."""
        for vals in vals_list:
            if not vals.get("company_id"):
                vals["company_id"] = self.env.company.id
            if not vals.get("source_url") and vals.get("codigo"):
                vals["source_url"] = self._build_url(
                    vals["codigo"], vals.get("process_type", "licitacion")
                )
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # Cron methods
    # -------------------------------------------------------------------------

    @api.model
    def cron_automatic_cleanup(self):
        """
        Deletes old 'no_apta' records that exceed the configured retention period.

        Only removes records without an associated CRM opportunity to prevent
        accidental data loss on converted tenders.
        """
        config = self.env.company
        retention_days = config.mercadopublico_retention_days_rejected or 30
        cutoff_date = fields.Datetime.now() - timedelta(days=retention_days)
        self.search([
            ("filter_decision", "=", "no_apta"),
            ("opportunity_id", "=", False),
            ("create_date", "<", cutoff_date),
        ]).unlink()

    @api.model
    def cron_archive_expired_tenders(self):
        """
        Moves expired published tenders to the 'descartada' stage and marks them closed.

        Tenders already in 'convertida' or 'descartada' stages are excluded to
        avoid overwriting intentional pipeline placements.
        """
        now = fields.Datetime.now()
        stage_discarded = self.env.ref(
            "mercadopublico_odoo_integration.etapa_descartada", raise_if_not_found=False
        )
        stage_converted = self.env.ref(
            "mercadopublico_odoo_integration.etapa_convertida", raise_if_not_found=False
        )
        excluded_stage_ids = [s.id for s in [stage_converted, stage_discarded] if s]
        expired = self.search([
            ("fecha_cierre", "<", now),
            ("estado", "in", ["publicada"]),
            ("stage_id", "not in", excluded_stage_ids),
        ])
        if stage_discarded:
            expired.write({
                "estado": "cerrada",
                "stage_id": stage_discarded.id,
                "discard_reason": "Archivada automáticamente por expiración",
            })
