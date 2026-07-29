"""
Public buyer agency (organismo público) model for Mercado Público integration.

Agencies are synced from the ChileCompra API via ``sync_buyers`` and
can be marked as favorites to influence the scoring and filtering pipeline.
"""
from odoo import models, fields


class MercadoPublicoBuyer(models.Model):
    """Represents a public buyer agency registered in the ChileCompra system."""

    _name = "mercadopublico.buyer"
    _description = "Organismo Público de Mercado Público"
    _order = "name"

    name = fields.Char("Nombre del Organismo", required=True, index=True)
    codigo = fields.Char("Código del Organismo", required=True, index=True)
    is_favorite = fields.Boolean("Favorito", default=False, index=True)
    active = fields.Boolean("Activo", default=True)

    _codigo_uniq = models.Constraint(
        "unique(codigo)", "El código del organismo debe ser único."
    )
