from odoo import models, fields

class MercadoPublicoLicitacionItem(models.Model):
    _name = 'mercadopublico.licitacion.item'
    _description = 'Ítem de Licitación o Compra Ágil'

    licitacion_id = fields.Many2one('mercadopublico.licitacion', string='Proceso', required=True, ondelete='cascade')
    codigo_producto = fields.Char('Código de Producto')
    codigo_categoria = fields.Char('Código de Categoría')
    is_match = fields.Boolean('Coincidencia', help='Indica si este ítem fue el que disparó el filtro positivo.')
    name = fields.Char('Nombre del Producto / Servicio')
    descripcion = fields.Text('Descripción')
    cantidad = fields.Float('Cantidad')
    unidad_medida = fields.Char('Unidad de Medida')
