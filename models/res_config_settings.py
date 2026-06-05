from odoo import models, fields
import pytz
from datetime import datetime, timedelta
import logging
from .mercadopublico_api import FUZZY_AVAILABLE

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mercadopublico_api_ticket = fields.Char(related='company_id.mercadopublico_api_ticket', readonly=False)
    mercadopublico_dias_busqueda_atras = fields.Integer(related='company_id.mercadopublico_dias_busqueda_atras', readonly=False)
    
    mercadopublico_sincronizar_licitaciones = fields.Boolean(related='company_id.mercadopublico_sincronizar_licitaciones', readonly=False)
    mercadopublico_sincronizar_compra_agil = fields.Boolean(related='company_id.mercadopublico_sincronizar_compra_agil', readonly=False)
    
    # Cuota API
    mercadopublico_api_limite = fields.Integer(related='company_id.mercadopublico_api_limite', readonly=False)
    mercadopublico_api_realizados = fields.Integer(related='company_id.mercadopublico_api_realizados', readonly=True)
    mercadopublico_api_reset = fields.Datetime(related='company_id.mercadopublico_api_reset', readonly=True)
    mercadopublico_v2_bloqueado_hasta = fields.Datetime(related='company_id.mercadopublico_v2_bloqueado_hasta', readonly=True)

    # Notificaciones
    mercadopublico_discuss_channel_id = fields.Many2one('discuss.channel', related='company_id.mercadopublico_discuss_channel_id', readonly=False)

    # Organismos
    mercadopublico_filtro_organismo_favorito = fields.Selection(related='company_id.mercadopublico_filtro_organismo_favorito', readonly=False)
    
    # Ubicaciones
    mercadopublico_modo_ubicacion = fields.Selection(related='company_id.mercadopublico_modo_ubicacion', readonly=False)
    mercadopublico_ubicacion_ids = fields.Many2many(related='company_id.mercadopublico_ubicacion_ids', readonly=False)

    mercadopublico_filtro_categoria_ids = fields.Many2many(related='company_id.mercadopublico_filtro_categoria_ids', readonly=False)
    mercadopublico_filtro_keyword_ids = fields.Many2many(related='company_id.mercadopublico_filtro_keyword_ids', readonly=False)
    mercadopublico_auto_import_tags = fields.Boolean(related='company_id.mercadopublico_auto_import_tags', readonly=False)

    # CRM
    mercadopublico_crm_team_id = fields.Many2one(related='company_id.mercadopublico_crm_team_id', readonly=False)
    mercadopublico_crm_user_id = fields.Many2one(related='company_id.mercadopublico_crm_user_id', readonly=False)

    # Configuración de Limpieza y Tareas
    mercadopublico_cron_hour = fields.Float(related='company_id.mercadopublico_cron_hour', readonly=False)
    mercadopublico_dias_retencion_no_aptas = fields.Integer(related='company_id.mercadopublico_dias_retencion_no_aptas', readonly=False)

    def set_values(self):
        super(ResConfigSettings, self).set_values()

        cron = self.env.ref('MercadoPublico-Odoo.ir_cron_mercadopublico_importar_licitaciones', raise_if_not_found=False)
        if cron:
            hour = int(self.mercadopublico_cron_hour)
            minute = int((self.mercadopublico_cron_hour - hour) * 60)
            
            tz_name = self.env.user.tz or 'America/Santiago'
            user_tz = pytz.timezone(tz_name)
            
            now_user = datetime.now(pytz.utc).astimezone(user_tz)
            
            next_call = now_user.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_call <= now_user:
                next_call += timedelta(days=1)
                
            next_call_utc = next_call.astimezone(pytz.utc).replace(tzinfo=None)
            cron.sudo().write({'nextcall': next_call_utc})

    # Status de librerias
    mercadopublico_status_libraries = fields.Selection([
        ('ok', 'Instaladas'),
        ('missing', 'Faltan')
    ], default=lambda self: 'ok' if FUZZY_AVAILABLE else 'missing')

    def action_get_api_key(self):
        return {'type': 'ir.actions.act_url', 'url': 'https://www.chilecompra.cl/api/', 'target': 'new'}

