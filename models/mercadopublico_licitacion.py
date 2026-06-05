from odoo import models, fields, api, _
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class MercadoPublicoLicitacion(models.Model):
    _name = 'mercadopublico.licitacion'
    _description = 'Licitación / Compra Ágil de Mercado Público'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_publicacion desc'

    name = fields.Char('Nombre', required=True, tracking=True)
    codigo = fields.Char('Código', required=True, tracking=True)
    descripcion = fields.Text('Descripción', tracking=True)
    
    tipo_proceso = fields.Selection([
        ('licitacion', 'Licitación Pública (v1)'),
        ('compra_agil', 'Compra Ágil (v2)')
    ], string='Tipo de Proceso', default='licitacion', required=True, tracking=True)
    
    estado = fields.Selection([
        ('publicada', 'Publicada'),
        ('cerrada', 'Cerrada'),
        ('desierta', 'Desierta'),
        ('adjudicada', 'Adjudicada'),
        ('revocada', 'Revocada'),
        ('suspendida', 'Suspendida'),
        ('proveedor_seleccionado', 'Proveedor Seleccionado (CA)')
    ], string='Estado', tracking=True)
    
    # Fechas
    fecha_publicacion = fields.Datetime('Fecha Publicación', tracking=True)
    fecha_cierre = fields.Datetime('Fecha Cierre', tracking=True)
    fecha_adjudicacion = fields.Datetime('Fecha Adjudicación', tracking=True)
    
    # Organismo
    comprador_codigo = fields.Char('Código Organismo', tracking=True)
    comprador_nombre = fields.Char('Nombre Organismo', tracking=True)
    comprador_comuna = fields.Char('Comuna', tracking=True)
    comprador_region = fields.Char('Región', tracking=True)
    
    organismo_id = fields.Many2one('mercadopublico.organismo', string='Organismo', compute='_compute_organismo_id', store=True)
    organismo_favorito = fields.Boolean(related='organismo_id.favorito', string='Organismo Favorito', readonly=False)

    # Detalles
    moneda = fields.Char('Moneda', tracking=True)
    monto_estimado = fields.Float('Monto Estimado', tracking=True)
    url_mercado_publico = fields.Char('URL Mercado Público', tracking=True)
    tipo_licitacion = fields.Char('Tipo Licitación', tracking=True)
    etapas = fields.Integer('Etapas', tracking=True)
    etapas_estado = fields.Char('Estado de Etapas', readonly=True, tracking=True)
    toma_razon = fields.Boolean('Requiere Toma de Razón', readonly=True, tracking=True)
    fuente_financiamiento = fields.Char('Fuente Financiamiento', readonly=True, tracking=True)

    # Clasificación (Tier 1)
    categoria_ids = fields.Many2many('mercadopublico.categoria', string='Categorías UNSPSC', tracking=True)
    item_ids = fields.One2many('mercadopublico.licitacion.item', 'licitacion_id', string='Productos/Ítems')
    palabras_clave_encontradas = fields.Text('Palabras clave encontradas')
    rating = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
    ], string='Relevancia', default='0', tracking=True)

    # Análisis y Estados
    state = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('analizando', 'Analizando'),
        ('analizado', 'Analizado')
    ], string='Estado de Procesamiento', default='nuevo', index=True, tracking=True)
    
    decision_filtro = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('apta', 'Apta'),
        ('no_apta', 'No Apta')
    ], string='Decisión de Filtro', default='pendiente', index=True, tracking=True)

    etapa_id = fields.Many2one('mercadopublico.etapa', string='Etapa', tracking=True, group_expand='_read_group_stage_ids')
    
    @api.model
    def _read_group_stage_ids(self, stages, domain):
        return stages.search([])

    @staticmethod
    def _build_url(codigo, tipo_proceso):
        if tipo_proceso == 'licitacion':
            return f"https://www.mercadopublico.cl/fichaLicitacion.html?idLicitacion={codigo}"
        return f"https://www.mercadopublico.cl/Home/FichaCompraAgil/{codigo}"
    
    motivo_descarte = fields.Text('Motivo de descarte', tracking=True)
    opportunity_id = fields.Many2one('crm.lead', 'Oportunidad', tracking=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, tracking=True)

    _sql_constraints = [('codigo_uniq', 'unique(codigo, company_id)', 'El código del proceso debe ser único por compañía')]

    @api.depends('comprador_codigo')
    def _compute_organismo_id(self):
        for licitacion in self:
            if licitacion.comprador_codigo:
                organismo = self.env['mercadopublico.organismo'].search([('codigo', '=', licitacion.comprador_codigo)], limit=1)
                licitacion.organismo_id = organismo.id
            else:
                licitacion.organismo_id = False

    def action_toggle_organismo_favorito(self):
        self.ensure_one()
        if not self.comprador_codigo: return
        organismo = self.env['mercadopublico.organismo'].search([('codigo', '=', self.comprador_codigo)], limit=1)
        if not organismo:
            organismo = self.env['mercadopublico.organismo'].create({'name': self.comprador_nombre, 'codigo': self.comprador_codigo, 'favorito': True})
        else:
            organismo.favorito = not organismo.favorito
        return True
    
    def action_descartar(self):
        return {
            'name': _('Feedback de Licitación'),
            'type': 'ir.actions.act_window',
            'res_model': 'mercadopublico.licitacion.descartar.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_licitacion_id': self.id, 'default_tipo_accion': 'no_apta'}
        }

    def action_marcar_apta(self):
        return {
            'name': _('Feedback de Licitación'),
            'type': 'ir.actions.act_window',
            'res_model': 'mercadopublico.licitacion.descartar.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_licitacion_id': self.id, 'default_tipo_accion': 'apta'}
        }
    
    def action_convertir_oportunidad(self):
        self.ensure_one()
        etapa_convertida = self.env.ref('MercadoPublico-Odoo.etapa_convertida', raise_if_not_found=False)
        if self.opportunity_id:
            return {'type': 'ir.actions.act_window', 'res_model': 'crm.lead', 'res_id': self.opportunity_id.id, 'view_mode': 'form', 'target': 'current'}
        opportunity_vals = {
            'name': f"{dict(self._fields['tipo_proceso'].selection).get(self.tipo_proceso)}: {self.name}", 
            'description': self.descripcion, 
            'type': 'opportunity', 
            'partner_name': self.comprador_nombre,
            'city': self.comprador_comuna, 
            'mercadopublico_id': self.id, 
            'mercadopublico_codigo': self.codigo, 
            'mercadopublico_fecha_cierre': self.fecha_cierre, 
            'is_mercadopublico': True,
        }
        
        company = self.env.company
        if company.mercadopublico_crm_team_id:
            opportunity_vals['team_id'] = company.mercadopublico_crm_team_id.id
        if company.mercadopublico_crm_user_id:
            opportunity_vals['user_id'] = company.mercadopublico_crm_user_id.id

        opportunity = self.env['crm.lead'].create(opportunity_vals)
        vals = {'opportunity_id': opportunity.id}
        if etapa_convertida: vals['etapa_id'] = etapa_convertida.id
        self.write(vals)
        return {'type': 'ir.actions.act_window', 'res_model': 'crm.lead', 'res_id': opportunity.id, 'view_mode': 'form', 'target': 'current'}
    
    def action_abrir_mercadopublico(self):
        self.ensure_one()
        if not self.url_mercado_publico:
            self.url_mercado_publico = self._build_url(self.codigo, self.tipo_proceso)
        return {'type': 'ir.actions.act_url', 'url': self.url_mercado_publico, 'target': 'new'}

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('company_id'): vals['company_id'] = self.env.company.id
            if not vals.get('url_mercado_publico') and vals.get('codigo'):
                vals['url_mercado_publico'] = self._build_url(vals['codigo'], vals.get('tipo_proceso', 'licitacion'))
        return super().create(vals_list)

    @api.model
    def cron_limpieza_automatica(self):
        config = self.env.company
        fecha_limite = fields.Datetime.now() - timedelta(days=config.mercadopublico_dias_retencion_no_aptas or 30)
        self.search([('decision_filtro', '=', 'no_apta'), ('opportunity_id', '=', False), ('create_date', '<', fecha_limite)]).unlink()

    @api.model
    def cron_archivar_licitaciones_expiradas(self):
        hoy = fields.Datetime.now()
        etapa_descartada = self.env.ref('MercadoPublico-Odoo.etapa_descartada', raise_if_not_found=False)
        etapa_convertida = self.env.ref('MercadoPublico-Odoo.etapa_convertida', raise_if_not_found=False)
        excluir_ids = [e.id for e in [etapa_convertida, etapa_descartada] if e]
        licitaciones = self.search([('fecha_cierre', '<', hoy), ('estado', 'in', ['publicada']), ('etapa_id', 'not in', excluir_ids)])
        if etapa_descartada: licitaciones.write({'estado': 'cerrada', 'etapa_id': etapa_descartada.id, 'motivo_descarte': 'Archivada automáticamente por expiración'})
