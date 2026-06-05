from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = 'product.category'

    mercadopublico_categoria_ids = fields.Many2many(
        'mercadopublico.categoria',
        'product_category_mercadopublico_rel',
        string='Categorías Mercado Público (UNSPSC)'
    )

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    mercadopublico_categoria_ids = fields.Many2many(
        'mercadopublico.categoria',
        'product_template_mercadopublico_rel',
        string='Categorías Mercado Público (Propias)'
    )

    todas_mercadopublico_categoria_ids = fields.Many2many(
        'mercadopublico.categoria',
        compute='_compute_todas_mercadopublico_categoria_ids',
        string='Categorías Mercado Público (Efectivas)'
    )

    @api.depends('mercadopublico_categoria_ids', 'categ_id.mercadopublico_categoria_ids')
    def _compute_todas_mercadopublico_categoria_ids(self):
        for product in self:
            categorias = product.mercadopublico_categoria_ids
            if product.categ_id and product.categ_id.mercadopublico_categoria_ids:
                categorias |= product.categ_id.mercadopublico_categoria_ids
            product.todas_mercadopublico_categoria_ids = categorias

class ProductTag(models.Model):
    _inherit = 'product.tag'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self.env.company.mercadopublico_auto_import_tags:
            existing = set(self.env['mercadopublico.filtro'].search([]).mapped('keyword'))
            new_filtros = [{'keyword': tag.name, 'active': True} for tag in records if tag.name and tag.name not in existing]
            if new_filtros:
                created = self.env['mercadopublico.filtro'].create(new_filtros)
                self.env.company.mercadopublico_filtro_keyword_ids = [(4, f.id) for f in created]
        return records
