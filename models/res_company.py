"""
Extension of res.company with Mercado Público integration configuration fields.

All integration settings are stored on the company record to support
multi-company environments. The ResConfigSettings model provides the
user-facing form proxied via related fields.
"""
from odoo import models, fields, api


class ResCompany(models.Model):
    """Extends res.company with Mercado Público API credentials and filter settings."""

    _inherit = "res.company"

    # -------------------------------------------------------------------------
    # API credentials
    # -------------------------------------------------------------------------

    mercadopublico_api_ticket = fields.Char(
        "Ticket de API",
        help=(
            "Su clave de conexión con Mercado Público. "
            "Se obtiene gratis en la página de ChileCompra (api.mercadopublico.cl)."
        ),
    )
    mercadopublico_search_days_backward = fields.Integer(
        "Días de búsqueda hacia atrás",
        default=0,
        help=(
            "Permite buscar oportunidades publicadas en días anteriores. "
            "(Ej: 0 = busca sólo lo de hoy. 1 = busca también lo de ayer)."
        ),
    )

    # -------------------------------------------------------------------------
    # Sync toggles
    # -------------------------------------------------------------------------

    mercadopublico_sync_tenders = fields.Boolean(
        "Sincronizar Licitaciones Públicas",
        default=True,
        help="Active esta opción para descargar y evaluar automáticamente las grandes licitaciones públicas (v1).",
    )
    mercadopublico_sync_quick_buys = fields.Boolean(
        "Sincronizar Compras Ágiles",
        default=True,
        help="Active esta opción para descargar y evaluar diariamente las oportunidades de compra directa de menor tamaño (v2).",
    )

    # -------------------------------------------------------------------------
    # API rate limiting and quota control
    # -------------------------------------------------------------------------

    mercadopublico_api_limit = fields.Integer(
        "Límite Diario API",
        default=10000,
        help="Límite máximo de peticiones a la API por día (estimado).",
    )
    mercadopublico_api_success = fields.Integer(
        "Llamadas Exitosas",
        default=0,
    )
    mercadopublico_api_fail = fields.Integer(
        "Llamadas Fallidas",
        default=0,
    )
    mercadopublico_api_realizados = fields.Integer(
        "Requests Realizados",
        default=0,
        compute="_compute_api_realizados",
        help="Contador local de peticiones realizadas hoy.",
    )
    mercadopublico_api_reset = fields.Datetime(
        "Próximo Reset de Cuota",
        help="Fecha y hora de reinicio del contador.",
    )
    mercadopublico_is_syncing = fields.Boolean(
        "Sincronización en Curso",
        default=False,
        help="Indica si existe un proceso de descubrimiento/sincronización activo.",
    )
    mercadopublico_sync_start_time = fields.Datetime(
        "Hora Inicio Sincronización",
        help="Marca temporal del inicio de la sincronización para liberar bloqueos huérfanos.",
    )
    mercadopublico_cron_analysis_minutes = fields.Integer(
        "Frecuencia Cron de Análisis (min)",
        default=2,
        help="Cada cuántos minutos se ejecutará el procesamiento de la cola de licitaciones.",
    )
    mercadopublico_v2_ttl_minutes = fields.Integer(
        "TTL Búsqueda Compras Ágiles (min)",
        default=60,
        help="Ventana de tiempo en minutos para consultar Compras Ágiles recientes (ttl_cambio_ms).",
    )
    mercadopublico_status_update_interval_hours = fields.Integer(
        "Frecuencia Cron de Actualización de Estado (horas)",
        default=2,
        help="Cada cuántas horas se actualizará el estado de las licitaciones en seguimiento.",
    )
    mercadopublico_strict_buyer_mode = fields.Boolean(
        "Filtro Estricto en Cabecera para Organismos Favoritos",
        default=False,
        help=(
            "Si está activo, en modo excluyente se descartarán en memoria desde la cabecera "
            "los registros que no pertenezcan a los organismos favoritos."
        ),
    )

    # -------------------------------------------------------------------------
    # Notifications
    # -------------------------------------------------------------------------

    def _default_mercadopublico_discuss_channel_id(self):
        return self.env.ref(
            "mercadopublico_odoo_integration.channel_mercadopublico",
            raise_if_not_found=False,
        )

    mercadopublico_discuss_channel_id = fields.Many2one(
        "discuss.channel",
        string="Canal de Notificaciones",
        default=_default_mercadopublico_discuss_channel_id,
        help=(
            "Canal interno de comunicación (Discuss) donde el sistema le notificará "
            "automáticamente cada vez que encuentre una oportunidad de negocio apta."
        ),
    )

    # -------------------------------------------------------------------------
    # Filter configuration
    # -------------------------------------------------------------------------

    mercadopublico_keyword_organismo_favorito = fields.Selection(
        [
            ("desactivado", "Desactivado (No filtrar)"),
            ("aditivo", "Aditivo (+1 Estrella a favoritos)"),
            ("excluyente", "Excluyente (Solo acepta favoritos)"),
        ],
        string="Modo Filtro Organismos",
        default="desactivado",
        help="Define si deseas darle prioridad o exclusividad a los organismos públicos que has marcado como favoritos.",
    )
    mercadopublico_location_mode = fields.Selection(
        [
            ("desactivado", "Desactivado (No filtrar)"),
            ("aditivo", "Aditivo (+1 Estrella a ubicaciones deseadas)"),
            ("excluyente", "Excluyente (Solo acepta ubicaciones deseadas)"),
        ],
        string="Modo Filtro Ubicaciones",
        default="desactivado",
        help="Regla global para filtrar licitaciones según la ubicación del comprador.",
    )
    mercadopublico_location_ids = fields.Many2many(
        "mercadopublico.location",
        "res_company_location_rel",
        string="Ubicaciones Deseadas",
        help="Regiones o Comunas específicas en las que te interesa vender.",
    )
    mercadopublico_category_ids = fields.Many2many(
        "mercadopublico.category",
        "res_company_category_rel",
        string="Categorías a Sincronizar",
        help="Si está vacío, se sincronizarán todas.",
    )
    mercadopublico_keyword_ids = fields.Many2many(
        "mercadopublico.keyword",
        "res_company_keyword_rel",
        string="Palabras Clave (Filtro IA)",
        help="Solo se importarán las licitaciones que hagan match con estas palabras clave.",
    )
    mercadopublico_auto_import_tags = fields.Boolean(
        "Importar automáticamente nuevos Tags como Palabras Clave",
        default=False,
        help=(
            "Si está activo, cada vez que se crea un nuevo tag de producto en Odoo, "
            "se importa automáticamente como palabra clave de Mercado Público."
        ),
    )

    # -------------------------------------------------------------------------
    # CRM defaults
    # -------------------------------------------------------------------------

    mercadopublico_crm_team_id = fields.Many2one(
        "crm.team",
        string="Equipo de Ventas",
        help="Equipo de ventas al que se le asignarán por defecto las nuevas oportunidades provenientes de Mercado Público.",
    )
    mercadopublico_crm_user_id = fields.Many2one(
        "res.users",
        string="Vendedor Asignado",
        domain="[('share', '=', False)]",
        help="Persona que quedará como responsable de la oportunidad al momento de crearla.",
    )

    # -------------------------------------------------------------------------
    # Maintenance / retention
    # -------------------------------------------------------------------------

    mercadopublico_cron_hour = fields.Float(
        string="Hora de Sincronización",
        default=23.0,
        help="Hora del día en la que se ejecutará la descarga automática de licitaciones.",
    )
    mercadopublico_retention_days_rejected = fields.Integer(
        "Días de retención (No Aptas)",
        default=30,
        help=(
            "Días que se conservarán en la base de datos las licitaciones descartadas "
            "antes de ser eliminadas automáticamente para ahorrar espacio."
        ),
    )

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def action_sync_buyers(self):
        """Triggers a manual buyer agency sync and displays a confirmation notification."""
        self.env["mercadopublico.api"].sync_buyers()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Sincronización Iniciada",
                "message": "Se ha disparado la sincronización de organismos.",
                "type": "success",
                "sticky": False,
            },
        }


    @api.depends("mercadopublico_api_success", "mercadopublico_api_fail")
    def _compute_api_realizados(self):
        for record in self:
            record.mercadopublico_api_realizados = record.mercadopublico_api_success + record.mercadopublico_api_fail
