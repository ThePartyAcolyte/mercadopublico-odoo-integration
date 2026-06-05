from odoo import models, fields, api

class MercadoPublicoUbicacion(models.Model):
    _name = 'mercadopublico.ubicacion'
    _description = 'Ubicación (Región/Comuna) de Chile'
    _order = 'name'
    _parent_store = True
    _parent_name = "parent_id"

    name = fields.Char('Nombre', required=True, index=True)
    tipo = fields.Selection([
        ('region', 'Región'),
        ('comuna', 'Comuna')
    ], string='Tipo', required=True)
    parent_id = fields.Many2one('mercadopublico.ubicacion', string='Región Padre', index=True, domain=[('tipo', '=', 'region')])
    child_ids = fields.One2many('mercadopublico.ubicacion', 'parent_id', string='Comunas')
    parent_path = fields.Char(index=True, unaccent=False)
    active = fields.Boolean('Activo', default=True)

    @api.depends('name', 'parent_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.tipo == 'comuna' and record.parent_id:
                record.display_name = f"{record.name} ({record.parent_id.name})"
            else:
                record.display_name = record.name
