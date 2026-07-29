"""
Onboarding wizard for the Mercado Público integration module.

Guides the user through the initial configuration in a single-form flow:
API credentials, sync toggles, keyword/category filters, and CRM defaults.
Displayed when the integration is installed and no API ticket is configured.
"""
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..models.services.scoring import FUZZY_AVAILABLE

_logger = logging.getLogger(__name__)


class MercadoPublicoOnboardingWizard(models.TransientModel):
    """
    Transient wizard for guided initial setup of the Mercado Público integration.

    Writes all user inputs directly to ``res.company`` on completion.
    """

    _name = "mercadopublico.onboarding.wizard"
    _description = "Onboarding de Mercado Público"

    api_ticket = fields.Char(
        "Ticket de API",
        help="Su clave de conexión con Mercado Público. Se obtiene gratis en la página de ChileCompra.",
    )
    sincronizar_licitaciones = fields.Boolean(
        "Sincronizar Licitaciones Públicas",
        default=True,
        help="Active esta opción para descargar y evaluar automáticamente las licitaciones públicas.",
    )
    sincronizar_compra_agil = fields.Boolean(
        "Sincronizar Compras Ágiles",
        default=True,
        help="Active esta opción para descargar y evaluar diariamente las oportunidades de compra de menor tamaño (Compra Ágil).",
    )
    mercadopublico_keyword_ids = fields.Many2many(
        "mercadopublico.keyword",
        "onboarding_keyword_new_rel",
        string="Palabras Clave",
        help="Términos específicos (ej: 'notebook', 'software') que definen sus productos o servicios.",
    )
    import_tag_ids = fields.Many2many(
        "crm.tag",
        "onboarding_tag_import_new_rel",
        string="Etiquetas (Tags) Seleccionadas",
        help="Selecciona los tags de producto existentes que quieres incorporar como palabras clave.",
    )
    mercadopublico_category_ids = fields.Many2many(
        "mercadopublico.category",
        "onboarding_cat_new_rel",
        string="Categorías (UNSPSC)",
        help="Rubros comerciales (UNSPSC) en los que su empresa participa.",
    )
    crm_team_id = fields.Many2one(
        "crm.team",
        string="Equipo de Ventas",
        help="Equipo de ventas al que se le asignarán por defecto las nuevas oportunidades.",
    )
    crm_user_id = fields.Many2one(
        "res.users",
        string="Vendedor Asignado",
        domain="[('share', '=', False)]",
        help="Persona que quedará como responsable de la oportunidad al momento de crearla.",
    )
    status_libraries = fields.Selection(
        [("ok", "Instaladas"), ("missing", "Faltan")],
        default=lambda self: "ok" if FUZZY_AVAILABLE else "missing",
    )

    @api.model
    def default_get(self, fields_list):
        """Pre-fills the form with existing company configuration values."""
        res = super().default_get(fields_list)
        company = self.env.company
        if "api_ticket" in fields_list:
            res["api_ticket"] = company.mercadopublico_api_ticket or ""
        if "sincronizar_licitaciones" in fields_list:
            res["sincronizar_licitaciones"] = company.mercadopublico_sync_tenders
        if "sincronizar_compra_agil" in fields_list:
            res["sincronizar_compra_agil"] = company.mercadopublico_sync_quick_buys
        if "crm_team_id" in fields_list:
            res["crm_team_id"] = company.mercadopublico_crm_team_id.id
        if "crm_user_id" in fields_list:
            res["crm_user_id"] = company.mercadopublico_crm_user_id.id
        return res

    def action_finish_onboarding(self):
        """
        Persists all wizard inputs to the current company and redirects to the dashboard.

        Raises:
            ValidationError: If the API ticket field is empty.
        """
        if not self.api_ticket:
            raise ValidationError(_("El Ticket de API es obligatorio para continuar."))

        company = self.env.company
        company.mercadopublico_api_ticket = self.api_ticket
        company.mercadopublico_sync_tenders = self.sincronizar_licitaciones
        company.mercadopublico_sync_quick_buys = self.sincronizar_compra_agil

        if self.crm_team_id:
            company.mercadopublico_crm_team_id = self.crm_team_id.id
        if self.crm_user_id:
            company.mercadopublico_crm_user_id = self.crm_user_id.id

        keyword_ids = list(self.mercadopublico_keyword_ids.ids)
        if self.import_tag_ids:
            existing_keywords = set(
                self.env["mercadopublico.keyword"].search([]).mapped("keyword")
            )
            new_keywords = [
                {"keyword": tag.name, "active": True}
                for tag in self.import_tag_ids
                if tag.name and tag.name not in existing_keywords
            ]
            if new_keywords:
                created = self.env["mercadopublico.keyword"].create(new_keywords)
                keyword_ids.extend(created.ids)

        if keyword_ids:
            company.mercadopublico_keyword_ids = [(6, 0, keyword_ids)]
        if self.mercadopublico_category_ids:
            company.mercadopublico_category_ids = [(6, 0, self.mercadopublico_category_ids.ids)]

        if self.env["mercadopublico.buyer"].search_count([]) == 0:
            self.env["mercadopublico.api"].sync_buyers()

        menu = self.env.ref("mercadopublico_odoo_integration.menu_mercadopublico_root")
        return {
            "type": "ir.actions.act_url",
            "url": f"/odoo/action-mercadopublico_odoo_integration.action_mercadopublico_dashboard_router?menu_id={menu.id}",
            "target": "self",
        }
