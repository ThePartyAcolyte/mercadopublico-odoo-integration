"""
Keyword filter model for Mercado Público tender matching.

Keywords are managed by the user through Settings and are evaluated against
tender names and descriptions by the scoring engine (scoring.py).
"""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class MercadoPublicoKeyword(models.Model):
    """Stores an individual keyword used to filter and score tender records."""

    _name = "mercadopublico.keyword"
    _description = "Palabra Clave de Búsqueda"
    _rec_name = "keyword"

    keyword = fields.Char("Palabra Clave", required=True)
    active = fields.Boolean("Activo", default=True)

    @api.constrains("keyword")
    def _check_keyword(self):
        """Validates that keyword is not empty or whitespace-only."""
        for record in self:
            if not record.keyword or not record.keyword.strip():
                raise ValidationError(_("La palabra clave no puede estar vacía."))
