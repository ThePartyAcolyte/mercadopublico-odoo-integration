from odoo import models, fields, api, _

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    # Campos para relacionar con licitaciones
    mercadopublico_id = fields.Many2one(
        'mercadopublico.licitacion',
        string='Licitación de Mercado Público',
        ondelete='set null',
        help='Licitación de Mercado Público relacionada con esta oportunidad'
    )
    mercadopublico_codigo = fields.Char(
        string='Código Licitación',
        readonly=True
    )
    mercadopublico_fecha_cierre = fields.Datetime(
        string='Fecha Cierre Licitación',
        readonly=True
    )
    
    # Indicador visual para licitaciones
    is_mercadopublico = fields.Boolean(
        string='Es de Mercado Público',
        compute='_compute_is_mercadopublico',
        store=True
    )
    
    @api.depends('mercadopublico_id')
    def _compute_is_mercadopublico(self):
        for lead in self:
            lead.is_mercadopublico = bool(lead.mercadopublico_id)
    
    @api.model_create_multi
    def create(self, vals_list):
        # Crear las oportunidades
        leads = super(CrmLead, self).create(vals_list)
        
        # Procesar cada registro creado
        for lead in leads:
            # Si tiene una licitación relacionada, actualizar datos adicionales
            if lead.mercadopublico_id:
                # Actualizar fecha de cierre de propuesta si no está establecida
                if not lead.date_deadline and lead.mercadopublico_fecha_cierre:
                    lead.date_deadline = lead.mercadopublico_fecha_cierre
                    
                # Añadir nota interna con enlace a la licitación
                url = lead.mercadopublico_id.url_mercado_publico
                if url:
                    lead.message_post(
                        body=_(
                            "Esta oportunidad fue creada desde la licitación de Mercado Público: "
                            "<a href='%s' target='_blank'>%s</a>"
                        ) % (url, lead.mercadopublico_codigo or lead.mercadopublico_id.codigo),
                        subject=_("Creado desde Mercado Público")
                    )
        
        return leads
    
    def action_view_mercadopublico_licitacion(self):
        """Acción para ver la licitación relacionada"""
        self.ensure_one()
        if not self.mercadopublico_id:
            return
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mercadopublico.licitacion',
            'res_id': self.mercadopublico_id.id,
            'view_mode': 'form',
            'target': 'current',
        }