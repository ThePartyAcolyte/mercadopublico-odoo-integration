from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    mercadopublico_api_ticket = fields.Char('Ticket de API', help="Su clave de conexión con Mercado Público. Se obtiene gratis en la página de ChileCompra (api.mercadopublico.cl).")
    mercadopublico_dias_busqueda_atras = fields.Integer(
        'Días de búsqueda hacia atrás', default=0,
        help="Permite buscar oportunidades publicadas en días anteriores. (Ej: 0 = busca sólo lo de hoy. 1 = busca también lo de ayer)."
    )
    
    mercadopublico_sincronizar_licitaciones = fields.Boolean('Sincronizar Licitaciones Públicas', default=True, help="Active esta opción para descargar y evaluar automáticamente las grandes licitaciones públicas (v1).")
    mercadopublico_sincronizar_compra_agil = fields.Boolean('Sincronizar Compras Ágiles', default=True, help="Active esta opción para descargar y evaluar diariamente las oportunidades de compra directa de menor tamaño (v2).")
    
    # Rate Limiting y Control de Cuota API
    mercadopublico_api_limite = fields.Integer("Límite Diario API", default=10000, help="Límite máximo de peticiones a la API por día (estimado).")
    mercadopublico_api_realizados = fields.Integer("Requests Realizados", default=0, help="Contador local de peticiones realizadas hoy.")
    mercadopublico_api_reset = fields.Datetime("Próximo Reset de Cuota", help="Fecha y hora de reinicio del contador.")
    mercadopublico_v2_bloqueado_hasta = fields.Datetime('Cuota API Bloqueada Hasta', help="Fecha y hora hasta la cual el sistema pausará las consultas para evitar bloqueos por cuota de la API (Error 429).")

    def _default_mercadopublico_discuss_channel_id(self):
        return self.env.ref('MercadoPublico-Odoo.channel_mercadopublico', raise_if_not_found=False)

    # Notificaciones
    mercadopublico_discuss_channel_id = fields.Many2one(
        'discuss.channel', 
        string='Canal de Notificaciones', 
        default=_default_mercadopublico_discuss_channel_id,
        help="Canal interno de comunicación (Discuss) donde el sistema le notificará automáticamente cada vez que encuentre una oportunidad de negocio apta."
    )

    mercadopublico_filtro_organismo_favorito = fields.Selection([
        ('desactivado', 'Desactivado (No filtrar)'),
        ('aditivo', 'Aditivo (+1 Estrella a favoritos)'),
        ('excluyente', 'Excluyente (Solo acepta favoritos)')
    ], string='Modo Filtro Organismos', default='desactivado', help="Define si deseas darle prioridad o exclusividad a los organismos públicos que has marcado como favoritos.")
    
    mercadopublico_modo_ubicacion = fields.Selection([
        ('desactivado', 'Desactivado (No filtrar)'),
        ('aditivo', 'Aditivo (+1 Estrella a ubicaciones deseadas)'),
        ('excluyente', 'Excluyente (Solo acepta ubicaciones deseadas)')
    ], string="Modo Filtro Ubicaciones", default='desactivado', help="Regla global para filtrar licitaciones según la ubicación del comprador.")
    
    mercadopublico_ubicacion_ids = fields.Many2many(
        'mercadopublico.ubicacion',
        'res_company_ubicacion_rel',
        string='Ubicaciones Deseadas',
        help="Regiones o Comunas específicas en las que te interesa vender."
    )

    mercadopublico_filtro_categoria_ids = fields.Many2many(
        'mercadopublico.categoria',
        'res_company_cat_filtro_rel',
        string='Categorías de Búsqueda',
        help="Rubros comerciales (UNSPSC) en los que su empresa participa. Las licitaciones de estas categorías tendrán mayor prioridad."
    )
    
    mercadopublico_filtro_keyword_ids = fields.Many2many(
        'mercadopublico.filtro',
        'res_company_filtro_keyword_rel',
        string='Palabras Clave',
        help="Términos específicos (ej: 'notebook', 'software') que definen sus productos o servicios."
    )
    
    mercadopublico_auto_import_tags = fields.Boolean(
        'Importar automáticamente nuevos Tags como Palabras Clave',
        default=False,
        help="Si está activo, cada vez que se crea un nuevo tag de producto en Odoo, se importa automáticamente como palabra clave de Mercado Público."
    )

    # CRM
    mercadopublico_crm_team_id = fields.Many2one(
        'crm.team', 
        string='Equipo de Ventas',
        help="Equipo de ventas al que se le asignarán por defecto las nuevas oportunidades provenientes de Mercado Público."
    )
    mercadopublico_crm_user_id = fields.Many2one(
        'res.users', 
        string='Vendedor Asignado',
        domain="[('share', '=', False)]",
        help="Persona que quedará como responsable de la oportunidad al momento de crearla."
    )

    # Configuración de Limpieza
    mercadopublico_cron_hour = fields.Float(
        string='Hora de Sincronización', 
        default=23.0, 
        help='Hora del día en la que se ejecutará la descarga automática de licitaciones.'
    )

    mercadopublico_dias_retencion_no_aptas = fields.Integer(
        'Días de retención (No Aptas)', 
        default=30,
        help="Días que se conservarán en la base de datos las licitaciones descartadas antes de ser eliminadas automáticamente para ahorrar espacio."
    )

    def action_sincronizar_organismos(self):
        self.env['mercadopublico.api'].sincronizar_organismos()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización Iniciada',
                'message': 'Se ha disparado la sincronización de organismos.',
                'type': 'success',
                'sticky': False,
            }
        }
