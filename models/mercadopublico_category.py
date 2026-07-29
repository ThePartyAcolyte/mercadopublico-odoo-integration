"""
UNSPSC category model for Mercado Público integration.

Categories are loaded from the ``mercadopublico_category_data.xml`` data file
during module installation. The hierarchical structure (family → class → commodity)
is represented via parent_store for efficient tree traversal.
"""
from odoo import api, models, fields


class MercadoPublicoCategory(models.Model):
    """
    Represents a UNSPSC (United Nations Standard Products and Services Code) category.

    Used to classify tender items and to configure the scoring filter on the
    company settings. Supports hierarchical browsing via parent_store.
    """

    _name = "mercadopublico.category"
    _description = "Categoría UNSPSC de Mercado Público"
    _parent_store = True
    _parent_name = "parent_id"
    _rec_name = "display_name"

    codigo = fields.Char("Código UNSPSC", required=True, index=True)
    name = fields.Char("Nombre", required=True)
    parent_id = fields.Many2one(
        "mercadopublico.category",
        string="Categoría Padre",
        index=True,
        ondelete="cascade",
    )
    child_ids = fields.One2many(
        "mercadopublico.category", "parent_id", string="Subcategorías"
    )
    parent_path = fields.Char(index=True)
    display_name = fields.Char(compute="_compute_display_name", store=True)

    _codigo_uniq = models.Constraint(
        "unique(codigo)", "El código UNSPSC debe ser único."
    )

    @api.depends("codigo", "name")
    def _compute_display_name(self):
        """Formats display_name as '[CODIGO] Nombre' for consistent UI rendering."""
        for record in self:
            record.display_name = f"[{record.codigo}] {record.name}"

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        """Extends name search to match against both code and name fields."""
        args = list(args or [])
        if name:
            args += ["|", ("codigo", operator, name), ("name", operator, name)]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def _load_records(self, data_list, update=False):
        """
        Disables tracking and defers parent_store computation during bulk data loads.

        This significantly speeds up the initial installation of the large
        UNSPSC category dataset (``mercadopublico_category_data.xml``).
        The ``super()`` call preserves the modified self context intentionally.
        """
        ctx_self = self.with_context(
            tracking_disable=True,
            defer_parent_store_computation=True,
        )
        return super(MercadoPublicoCategory, ctx_self)._load_records(
            data_list, update=update
        )
