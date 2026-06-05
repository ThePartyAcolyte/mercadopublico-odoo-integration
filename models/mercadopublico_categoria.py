from odoo import models, fields, api

class MercadoPublicoCategoria(models.Model):
    _name = 'mercadopublico.categoria'
    _description = 'Categoría UNSPSC de Mercado Público'
    _parent_store = True
    _parent_name = "parent_id"
    _rec_name = 'display_name'

    codigo = fields.Char('Código UNSPSC', required=True, index=True)
    name = fields.Char('Nombre', required=True)
    
    parent_id = fields.Many2one('mercadopublico.categoria', string='Categoría Padre', index=True, ondelete='cascade')
    child_ids = fields.One2many('mercadopublico.categoria', 'parent_id', string='Subcategorías')
    parent_path = fields.Char(index=True, unaccent=False)

    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('codigo', 'name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.codigo}] {record.name}"

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
        if name:
            args += ['|', ('codigo', operator, name), ('name', operator, name)]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)

    _sql_constraints = [
        ('codigo_uniq', 'unique(codigo)', 'El código UNSPSC debe ser único.')
    ]
