from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..models.mercadopublico_api import FUZZY_AVAILABLE
import logging

_logger = logging.getLogger(__name__)

class MercadoPublicoOnboardingWizard(models.TransientModel):
    _name = 'mercadopublico.onboarding.wizard'
    _description = 'Onboarding de Mercado Público'

    api_ticket = fields.Char('Ticket de API', help="Su clave de conexión con Mercado Público. Se obtiene gratis en la página de ChileCompra.")
    sincronizar_licitaciones = fields.Boolean('Sincronizar Licitaciones Públicas', default=True, help="Active esta opción para descargar y evaluar automáticamente las licitaciones públicas.")
    sincronizar_compra_agil = fields.Boolean('Sincronizar Compras Ágiles', default=True, help="Active esta opción para descargar y evaluar diariamente las oportunidades de compra de menor tamaño (Compra Ágil).")

    keyword_inclusions = fields.Many2many('mercadopublico.filtro', 'onboarding_keyword_rel', string='Palabras Clave', help="Términos específicos (ej: 'notebook', 'software') que definen sus productos o servicios.")
    import_tag_ids = fields.Many2many('product.tag', 'onboarding_tag_import_rel', string='Tags de Productos a Importar', help="Selecciona los tags de producto existentes que quieres incorporar como palabras clave de búsqueda en Mercado Público.")
    categoria_ids = fields.Many2many('mercadopublico.categoria', 'onboarding_cat_rel', string='Categorías a Incluir', help="Rubros comerciales (UNSPSC) en los que su empresa participa. Las licitaciones de estas categorías tendrán mayor prioridad.")

    crm_team_id = fields.Many2one('crm.team', string='Equipo de Ventas', help="Equipo de ventas al que se le asignarán por defecto las nuevas oportunidades.")
    crm_user_id = fields.Many2one('res.users', string='Vendedor Asignado', domain="[('share', '=', False)]", help="Persona que quedará como responsable de la oportunidad al momento de crearla.")

    status_libraries = fields.Selection([
        ('ok', 'Instaladas'),
        ('missing', 'Faltan')
    ], default=lambda self: 'ok' if FUZZY_AVAILABLE else 'missing')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        company = self.env.company
        if 'api_ticket' in fields_list:
            res['api_ticket'] = company.mercadopublico_api_ticket or ''
        if 'sincronizar_licitaciones' in fields_list:
            res['sincronizar_licitaciones'] = company.mercadopublico_sincronizar_licitaciones
        if 'sincronizar_compra_agil' in fields_list:
            res['sincronizar_compra_agil'] = company.mercadopublico_sincronizar_compra_agil
        if 'crm_team_id' in fields_list:
            res['crm_team_id'] = company.mercadopublico_crm_team_id.id
        if 'crm_user_id' in fields_list:
            res['crm_user_id'] = company.mercadopublico_crm_user_id.id
        return res

    def action_finish_onboarding(self):
        if not self.api_ticket:
            raise ValidationError("El Ticket de API es obligatorio para continuar.")

        company = self.env.company
        company.mercadopublico_api_ticket = self.api_ticket
        company.mercadopublico_sincronizar_licitaciones = self.sincronizar_licitaciones
        company.mercadopublico_sincronizar_compra_agil = self.sincronizar_compra_agil

        if self.crm_team_id:
            company.mercadopublico_crm_team_id = self.crm_team_id.id
        if self.crm_user_id:
            company.mercadopublico_crm_user_id = self.crm_user_id.id

        keyword_ids = list(self.keyword_inclusions.ids)

        if self.import_tag_ids:
            existing = set(self.env['mercadopublico.filtro'].search([]).mapped('keyword'))
            new_filtros = [{'keyword': tag.name, 'active': True} for tag in self.import_tag_ids if tag.name and tag.name not in existing]
            if new_filtros:
                created = self.env['mercadopublico.filtro'].create(new_filtros)
                keyword_ids.extend(created.ids)

        if keyword_ids:
            company.mercadopublico_filtro_keyword_ids = [(6, 0, keyword_ids)]

        if self.categoria_ids:
            company.mercadopublico_filtro_categoria_ids = [(6, 0, self.categoria_ids.ids)]

        if self.env['mercadopublico.organismo'].search_count([]) == 0:
            self.env['mercadopublico.api'].sincronizar_organismos()

        menu = self.env.ref('MercadoPublico-Odoo.menu_mercadopublico_root')
        return {
            'type': 'ir.actions.act_url',
            'url': f'/odoo/action-MercadoPublico-Odoo.action_mercadopublico_dashboard_router?menu_id={menu.id}',
            'target': 'self',
        }
