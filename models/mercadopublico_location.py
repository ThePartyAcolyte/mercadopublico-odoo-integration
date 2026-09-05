"""
Chilean region and commune location model for Mercado Público filtering.

Locations are pre-loaded from ``ubicaciones_chile.xml`` and used as filter
criteria in both the scoring pipeline and the v2 quick buy pre-filter.
The hierarchical structure (region → commune) is backed by parent_store.
"""
from odoo import api, models, fields


class MercadoPublicoLocation(models.Model):
    """Represents a Chilean administrative location (region or commune)."""

    _name = "mercadopublico.location"
    _description = "Ubicación (Región/Comuna) de Chile"
    _order = "name"
    _parent_store = True
    _parent_name = "parent_id"

    name = fields.Char("Nombre", required=True, index=True)
    codigo_region_api = fields.Integer(
        "ID Región API",
        index=True,
        help="Identificador numérico oficial de la región en la API de Mercado Público (ej. 13 para RM).",
    )
    tipo = fields.Selection(
        [("region", "Región"), ("comuna", "Comuna")],
        string="Tipo",
        required=True,
    )
    parent_id = fields.Many2one(
        "mercadopublico.location",
        string="Región Padre",
        index=True,
        domain=[("tipo", "=", "region")],
    )
    child_ids = fields.One2many(
        "mercadopublico.location", "parent_id", string="Comunas"
    )
    parent_path = fields.Char(index=True)
    active = fields.Boolean("Activo", default=True)

    @api.depends("name", "parent_id.name")
    def _compute_display_name(self):
        """Shows commune name with its parent region name for disambiguation."""
        for record in self:
            if record.tipo == "comuna" and record.parent_id:
                record.display_name = f"{record.name} ({record.parent_id.name})"
            else:
                record.display_name = record.name
