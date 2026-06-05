from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class MercadoPublicoLicitacionDescartarCategoria(models.TransientModel):
    _name = 'mercadopublico.licitacion.descartar.categoria'
    _description = 'Categoría Sugerida en Feedback'

    wizard_id = fields.Many2one('mercadopublico.licitacion.descartar.wizard', required=True, ondelete='cascade')
    categoria_id = fields.Many2one('mercadopublico.categoria', string='Categoría', required=True)
    seleccionar = fields.Boolean('Añadir', default=True)

class MercadoPublicoLicitacionDescartarWizard(models.TransientModel):
    _name = 'mercadopublico.licitacion.descartar.wizard'
    _description = 'Wizard de Feedback para Licitaciones'

    licitacion_id = fields.Many2one(
        'mercadopublico.licitacion', 
        string='Licitación',
        required=True
    )
    
    tipo_accion = fields.Selection([
        ('apta', 'Marcar como Apta'),
        ('no_apta', 'Descartar / No Apta')
    ], string='Acción', required=True)

    # Solo para descarte
    motivo_tipo = fields.Selection([
        ('filtro', 'No corresponde al rubro (Ajustar Filtro)'),
        ('catalogo', 'Productos solicitados no están en el catálogo'),
        ('tecnico', 'Falta de capacidad técnica'),
        ('economico', 'Falta de solvencia económica / Boletas'),
        ('plazo', 'Plazos imposibles'),
        ('dirigida', 'Marca o especificaciones exclusivas (Dirigida)'),
        ('presupuesto', 'Presupuesto estimado demasiado bajo'),
        ('ubicacion', 'Ubicación geográfica inviable'),
        ('conflicto', 'Conflicto de interés'),
        ('otro', 'Otro motivo')
    ], string='Motivo de descarte', default='filtro')
    
    comentario_adicional = fields.Text('Comentario / Motivo')

    categoria_line_ids = fields.One2many(
        'mercadopublico.licitacion.descartar.categoria',
        'wizard_id',
        string='Categorías Sugeridas'
    )

    @api.onchange('licitacion_id')
    def _onchange_licitacion_para_sugerencias(self):
        if not self.licitacion_id:
            self.categoria_line_ids = [(5, 0, 0)]
            return
            
        lic = self.licitacion_id
        sugeridas = self.env['mercadopublico.categoria']
        
        if lic.tipo_proceso == 'licitacion':
            sugeridas = lic.categoria_ids
        else:
            for item in lic.item_ids:
                if item.codigo_producto and len(item.codigo_producto) == 8:
                    familia_codigo = item.codigo_producto[:4] + "0000"
                    clase_codigo = item.codigo_producto[:6] + "00"
                    cat = self.env['mercadopublico.categoria'].search([
                        ('codigo', 'in', [clase_codigo, familia_codigo])
                    ], order='codigo desc', limit=1)
                    if cat:
                        sugeridas |= cat

        lines = [(5, 0, 0)]
        for cat in sugeridas:
            lines.append((0, 0, {
                'categoria_id': cat.id,
                'seleccionar': True
            }))
            
        self.categoria_line_ids = lines

    def action_confirmar(self):
        self.ensure_one()
        lic = self.licitacion_id
        
        # Actualizar la licitación
        motivo = dict(self._fields['motivo_tipo'].selection).get(self.motivo_tipo, '')
        if self.comentario_adicional:
            motivo = f"{motivo}: {self.comentario_adicional}"

        vals = {
            'decision_filtro': self.tipo_accion,
            'state': 'analizado'
        }

        if self.tipo_accion == 'no_apta':
            vals['motivo_descarte'] = motivo
            vals['rating'] = '0'
            etapa_desc = self.env.ref('MercadoPublico-Odoo.etapa_descartada', raise_if_not_found=False)
            if etapa_desc: vals['etapa_id'] = etapa_desc.id
        else:
            vals['rating'] = '3'
            etapa_espera = self.env.ref('MercadoPublico-Odoo.etapa_en_espera', raise_if_not_found=False)
            if etapa_espera: vals['etapa_id'] = etapa_espera.id

        lic.write(vals)
        
        # Log en el chatter
        msg = _("Decisión manual del usuario: <b>%s</b>.") % (self.tipo_accion.upper())
        
        # Añadir categorías sugeridas a la compañía si se solicitó
        if self.tipo_accion == 'apta':
            categorias_a_anadir = self.categoria_line_ids.filtered(lambda l: l.seleccionar).mapped('categoria_id')
            if categorias_a_anadir:
                self.env.company.mercadopublico_filtro_categoria_ids = [(4, cat.id) for cat in categorias_a_anadir]
                cats_names = ", ".join(categorias_a_anadir.mapped('name'))
                msg += _("<br/>Se añadieron las siguientes categorías a los filtros: <i>%s</i>") % cats_names
            
        lic.message_post(body=msg)

        return {'type': 'ir.actions.act_window_close'}
