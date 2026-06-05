from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class MercadoPublicoFiltro(models.Model):
    _name = 'mercadopublico.filtro'
    _description = 'Palabra Clave de Búsqueda'
    _rec_name = 'keyword'

    keyword = fields.Char('Palabra Clave', required=True)
    active = fields.Boolean('Activo', default=True)

    @api.constrains('keyword')
    def _check_keyword(self):
        for record in self:
            if not record.keyword or not record.keyword.strip():
                raise ValidationError(_('La palabra clave no puede estar vacía.'))
