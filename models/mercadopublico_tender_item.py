"""
Line item model for individual products or services within a tender or quick buy.

Items are extracted from the API detail payload and stored as child records of
``mercadopublico.tender``. The ``is_match`` flag indicates which items
triggered a positive keyword or category filter during scoring.
"""
from odoo import fields, models


class MercadoPublicoTenderItem(models.Model):
    """A single product or service line item within a tender or quick buy record."""

    _name = "mercadopublico.tender.item"
    _description = "Ítem de Licitación o Compra Ágil"

    tender_id = fields.Many2one(
        "mercadopublico.tender",
        string="Proceso",
        required=True,
        ondelete="cascade",
    )
    product_code = fields.Char("Código de Producto")
    category_code = fields.Char("Código de Categoría")
    is_match = fields.Boolean(
        "Coincidencia",
        help="Indica si este ítem fue el que disparó el filtro positivo.",
    )
    name = fields.Char("Nombre del Producto / Servicio")
    description = fields.Text("Descripción")
    quantity = fields.Float("Cantidad")
    unit_of_measure = fields.Char("Unidad de Medida")
