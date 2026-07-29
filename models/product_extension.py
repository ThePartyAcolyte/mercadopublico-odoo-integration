"""
Product and product category extensions for Mercado Público category mapping.

Adds UNSPSC category Many2many fields to both product.category and
product.template, allowing products to be associated with the UNSPSC taxonomy
used by the Mercado Público scoring pipeline.

Also extends product.tag to automatically create keyword filter records
when the ``mercadopublico_auto_import_tags`` company setting is enabled.
"""
from odoo import api, fields, models


class ProductCategory(models.Model):
    """Adds UNSPSC category mapping to product categories."""

    _inherit = "product.category"

    mercadopublico_category_ids = fields.Many2many(
        "mercadopublico.category",
        "product_category_mercadopublico_cat_rel",
        string="Categorías Mercado Público (UNSPSC)",
    )


class ProductTemplate(models.Model):
    """
    Adds UNSPSC category mapping to product templates.

    Provides both a direct mapping (``mercadopublico_category_ids``) and a
    computed effective mapping (``todas_mercadopublico_category_ids``) that
    merges the product's own categories with those inherited from its category.
    """

    _inherit = "product.template"

    mercadopublico_category_ids = fields.Many2many(
        "mercadopublico.category",
        "product_template_mercadopublico_cat_rel",
        string="Categorías Mercado Público (Propias)",
    )
    todas_mercadopublico_category_ids = fields.Many2many(
        "mercadopublico.category",
        compute="_compute_todas_mercadopublico_category_ids",
        string="Categorías Mercado Público (Efectivas)",
    )

    @api.depends("mercadopublico_category_ids", "categ_id.mercadopublico_category_ids")
    def _compute_todas_mercadopublico_category_ids(self):
        """
        Merges the product's own UNSPSC categories with those of its product category.

        This allows categories defined at the category level to propagate down
        to individual products without requiring per-product configuration.
        """
        for product in self:
            categories = product.mercadopublico_category_ids
            if product.categ_id and product.categ_id.mercadopublico_category_ids:
                categories |= product.categ_id.mercadopublico_category_ids
            product.todas_mercadopublico_category_ids = categories


class ProductTag(models.Model):
    """
    Extends product.tag to auto-import new tags as Mercado Público keywords.

    When ``mercadopublico_auto_import_tags`` is enabled on the company, any
    newly created product tag is automatically added as an active keyword
    filter in the scoring pipeline.
    """

    _inherit = "product.tag"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Creates product tags and conditionally imports them as MP keywords.

        Args:
            vals_list (list[dict]): List of field value dictionaries for the tags.

        Returns:
            recordset: The newly created product.tag records.
        """
        records = super().create(vals_list)
        if self.env.company.mercadopublico_auto_import_tags:
            existing_keywords = set(
                self.env["mercadopublico.keyword"].search([]).mapped("keyword")
            )
            new_keyword_vals = [
                {"keyword": tag.name, "active": True}
                for tag in records
                if tag.name and tag.name not in existing_keywords
            ]
            if new_keyword_vals:
                created = self.env["mercadopublico.keyword"].create(new_keyword_vals)
                self.env.company.mercadopublico_keyword_ids = [
                    (4, f.id) for f in created
                ]
        return records
