from odoo import models, fields

class MercadoPublicoOrganismo(models.Model):
    _name = 'mercadopublico.organismo'
    _description = 'Organismo Público de Mercado Público'
    _order = 'name'

    name = fields.Char('Nombre del Organismo', required=True, index=True)
    codigo = fields.Char('Código del Organismo', required=True, index=True)
    favorito = fields.Boolean('Favorito', default=False, index=True)
    active = fields.Boolean('Activo', default=True)

    _sql_constraints = [
        ('codigo_uniq', 'unique(codigo)', 'El código del organismo debe ser único')
    ]
