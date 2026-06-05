from odoo import models, fields, api

class MercadoPublicoDashboard(models.TransientModel):
    _name = 'mercadopublico.dashboard'
    _description = 'Dashboard de Mercado Público'

    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)

    # --- KPIs Dashboard ---
    kpi_licitaciones_hoy = fields.Integer(compute='_compute_kpis')
    kpi_compras_agiles_hoy = fields.Integer(compute='_compute_kpis')
    kpi_aptas_pendientes = fields.Integer(compute='_compute_kpis')
    kpi_monto_total_aptas = fields.Monetary(compute='_compute_kpis', string="Monto Estimado", currency_field='currency_id')
    kpi_tasa_aceptacion = fields.Float(compute='_compute_kpis')
    kpi_conversion_crm = fields.Float(compute='_compute_kpis')
    kpi_analisis_pendientes = fields.Integer(compute='_compute_kpis')

    kpi_licitaciones_progreso = fields.Float(compute='_compute_kpis')
    kpi_compras_agiles_progreso = fields.Float(compute='_compute_kpis')
    kpi_historico_analizados = fields.Integer(compute='_compute_kpis')
    kpi_historico_aptos = fields.Integer(compute='_compute_kpis')

    def _compute_kpis(self):
        hoy = fields.Date.today()
        Licitacion = self.env['mercadopublico.licitacion']
        for record in self:
            record.kpi_licitaciones_hoy = Licitacion.search_count([('create_date', '>=', hoy), ('tipo_proceso', '=', 'licitacion')])
            record.kpi_compras_agiles_hoy = Licitacion.search_count([('create_date', '>=', hoy), ('tipo_proceso', '=', 'compra_agil')])

            lic_analizadas_hoy = Licitacion.search_count([('create_date', '>=', hoy), ('tipo_proceso', '=', 'licitacion'), ('decision_filtro', '!=', 'pendiente')])
            record.kpi_licitaciones_progreso = (lic_analizadas_hoy / record.kpi_licitaciones_hoy) * 100 if record.kpi_licitaciones_hoy > 0 else 100.0

            ca_analizadas_hoy = Licitacion.search_count([('create_date', '>=', hoy), ('tipo_proceso', '=', 'compra_agil'), ('decision_filtro', '!=', 'pendiente')])
            record.kpi_compras_agiles_progreso = (ca_analizadas_hoy / record.kpi_compras_agiles_hoy) * 100 if record.kpi_compras_agiles_hoy > 0 else 100.0

            aptas_totales = Licitacion.search_count([('decision_filtro', '=', 'apta')])
            total_con_decision = Licitacion.search_count([('decision_filtro', 'in', ('apta', 'no_apta'))])

            record.kpi_tasa_aceptacion = (aptas_totales / total_con_decision) if total_con_decision > 0 else 0

            lic_aptas = Licitacion.search([('decision_filtro', '=', 'apta'), ('opportunity_id', '=', False)])
            record.kpi_monto_total_aptas = sum(lic_aptas.mapped('monto_estimado'))

            convertidas = Licitacion.search_count([('opportunity_id', '!=', False)])
            record.kpi_conversion_crm = (convertidas / aptas_totales) if aptas_totales > 0 else 0

            record.kpi_aptas_pendientes = Licitacion.search_count([('decision_filtro', '=', 'apta'), ('opportunity_id', '=', False)])
            record.kpi_analisis_pendientes = Licitacion.search_count([('decision_filtro', '=', 'pendiente')])

            record.kpi_historico_analizados = total_con_decision
            record.kpi_historico_aptos = aptas_totales

    @api.model
    def get_dashboard(self):
        return self.create({})
