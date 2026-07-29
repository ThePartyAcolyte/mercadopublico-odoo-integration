"""
Dashboard transient model for Mercado Público KPI display.

A new record is created on demand by ``get_dashboard`` and immediately
discarded after rendering — no persistent data is stored. All KPI fields
are computed on-the-fly against the live ``mercadopublico.tender`` table.
"""
from odoo import api, fields, models


class MercadoPublicoDashboard(models.TransientModel):
    """
    Transient model that aggregates KPI metrics for the Mercado Público dashboard.

    All compute fields query ``mercadopublico.tender`` at render time.
    The model instance is ephemeral and should be created via ``get_dashboard``.
    """

    _name = "mercadopublico.dashboard"
    _description = "Dashboard de Mercado Público"
    _rec_name = "name"

    name = fields.Char(
        string="Título", default="Dashboard Mercado Público", readonly=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
    )

    @api.depends("name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name or "Dashboard Mercado Público"

    # -------------------------------------------------------------------------
    # KPI fields — all computed, no storage
    # -------------------------------------------------------------------------

    kpi_licitaciones_hoy = fields.Integer(compute="_compute_kpis")
    kpi_compras_agiles_hoy = fields.Integer(compute="_compute_kpis")
    kpi_aptas_pendientes = fields.Integer(compute="_compute_kpis")
    kpi_monto_total_aptas = fields.Monetary(
        compute="_compute_kpis",
        string="Monto Estimado",
        currency_field="currency_id",
    )
    kpi_tasa_aceptacion = fields.Float(compute="_compute_kpis")
    kpi_conversion_crm = fields.Float(compute="_compute_kpis")
    kpi_analisis_pendientes = fields.Integer(compute="_compute_kpis")
    kpi_licitaciones_progreso = fields.Float(compute="_compute_kpis")
    kpi_compras_agiles_progreso = fields.Float(compute="_compute_kpis")
    kpi_historico_analizados = fields.Integer(compute="_compute_kpis")
    kpi_historico_aptos = fields.Integer(compute="_compute_kpis")

    def _compute_kpis(self):
        """Computes all dashboard KPIs in a single method to minimize ORM round-trips."""
        today = fields.Date.today()
        Tender = self.env["mercadopublico.tender"]
        for record in self:
            tenders_today = Tender.search_count(
                [("create_date", ">=", today), ("process_type", "=", "licitacion")]
            )
            quick_buys_today = Tender.search_count(
                [("create_date", ">=", today), ("process_type", "=", "compra_agil")]
            )
            record.kpi_licitaciones_hoy = tenders_today
            record.kpi_compras_agiles_hoy = quick_buys_today

            tenders_analyzed_today = Tender.search_count([
                ("create_date", ">=", today),
                ("process_type", "=", "licitacion"),
                ("filter_decision", "!=", "pendiente"),
            ])
            record.kpi_licitaciones_progreso = (
                (tenders_analyzed_today / tenders_today) * 100
                if tenders_today > 0
                else 100.0
            )

            quick_buys_analyzed_today = Tender.search_count([
                ("create_date", ">=", today),
                ("process_type", "=", "compra_agil"),
                ("filter_decision", "!=", "pendiente"),
            ])
            record.kpi_compras_agiles_progreso = (
                (quick_buys_analyzed_today / quick_buys_today) * 100
                if quick_buys_today > 0
                else 100.0
            )

            total_matched = Tender.search_count([("filter_decision", "=", "apta")])
            total_decided = Tender.search_count(
                [("filter_decision", "in", ("apta", "no_apta"))]
            )
            record.kpi_tasa_aceptacion = (
                total_matched / total_decided if total_decided > 0 else 0
            )

            matched_records = Tender.search(
                [("filter_decision", "=", "apta"), ("opportunity_id", "=", False)]
            )
            record.kpi_monto_total_aptas = sum(matched_records.mapped("estimated_amount"))

            converted = Tender.search_count([("opportunity_id", "!=", False)])
            record.kpi_conversion_crm = (
                converted / total_matched if total_matched > 0 else 0
            )

            record.kpi_aptas_pendientes = Tender.search_count(
                [("filter_decision", "=", "apta"), ("opportunity_id", "=", False)]
            )
            record.kpi_analisis_pendientes = Tender.search_count(
                [("filter_decision", "=", "pendiente")]
            )
            record.kpi_historico_analizados = total_decided
            record.kpi_historico_aptos = total_matched

    @api.model
    def get_dashboard(self):
        """
        Creates and returns a new ephemeral dashboard record.

        Returns:
            mercadopublico.dashboard: A new transient record with computed KPIs.
        """
        return self.create({"name": "Dashboard Mercado Público"})
