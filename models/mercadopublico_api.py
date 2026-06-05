from odoo import models, fields, api
import time
import requests
import random
import pytz
try:
    from thefuzz import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class MercadoPublicoAPI(models.AbstractModel):
    _name = 'mercadopublico.api'
    _description = 'API de Mercado Público (v1 y v2)'

    @api.model
    def _get_config(self):
        return self.env.company

    @api.model
    def _get_api_ticket(self):
        return self.env.company.mercadopublico_api_ticket

    # --- API v1: Licitaciones Públicas ---
    @api.model
    def get_licitaciones_by_date_v1(self, date_str, codigo_organismo=None):
        ticket = self._get_api_ticket()
        url = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
        params = {"fecha": date_str, "estado": "publicada", "ticket": ticket}
        if codigo_organismo: params['CodigoOrganismo'] = codigo_organismo
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            _logger.error(f"Error v1 licitaciones por fecha: {e}")
            return {"Listado": []}

    @api.model
    def get_licitacion_details_v1(self, codigo, max_retries=3):
        ticket = self._get_api_ticket()
        url = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
        params = {"codigo": codigo, "ticket": ticket}
        for retries in range(max_retries + 1):
            try:
                if retries > 0: time.sleep(2 ** retries + random.uniform(0, 1))
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 429: continue
                response.raise_for_status()
                data = response.json()
                if not data or 'Listado' not in data or not data['Listado']: return None
                return data['Listado'][0]
            except Exception as e:
                _logger.warning(f"Error detalle v1 {codigo} (intento {retries}): {e}")
        return None

    # --- Sincronización de Bloqueo V2 ---
    @api.model
    def _incrementar_consumo_api_v2(self):
        """Incrementa el contador local de consumo API y verifica reset diario."""
        company = self.env.company
        ahora = fields.Datetime.now()
        
        if not company.mercadopublico_api_reset or ahora >= company.mercadopublico_api_reset:
            ahora_utc = datetime.now(pytz.utc)
            chile_tz = pytz.timezone('America/Santiago')
            ahora_chile = ahora_utc.astimezone(chile_tz)
            manana_chile = (ahora_chile + timedelta(days=1)).replace(hour=0, minute=1, second=0)
            manana_utc = manana_chile.astimezone(pytz.utc).replace(tzinfo=None)
            
            company.mercadopublico_api_realizados = 0
            company.mercadopublico_api_reset = manana_utc
            
        company.mercadopublico_api_realizados += 1

    @api.model
    def _marcar_bloqueo_cuota_v2(self):
        # Bloquear temporalmente por 1 hora en lugar de hasta el día siguiente
        desbloqueo = fields.Datetime.now() + timedelta(hours=1)
        self.env.company.mercadopublico_v2_bloqueado_hasta = desbloqueo
        _logger.warning(f"Cuota API v2 (estimada/ráfaga) agotada. Bloqueando peticiones hasta {desbloqueo} UTC")

    # --- API v2: Compra Ágil ---
    @api.model
    def get_compras_agiles_v2(self, publicado_desde, publicado_hasta):
        ticket = self._get_api_ticket()
        url = "https://api2.mercadopublico.cl/v2/compra-agil"
        params = {
            "publicado_desde": publicado_desde,
            "publicado_hasta": publicado_hasta,
            "estado": "publicada",
            "tamano_pagina": 50,
            "numero_pagina": 1
        }
        all_items = []
        try:
            max_retries_pag = 3
            retries_pag = 0
            while True:
                self._incrementar_consumo_api_v2()
                response = requests.get(url, headers={'ticket': ticket}, params=params, timeout=20)
                
                if response.status_code == 429:
                    if retries_pag >= max_retries_pag:
                        self._marcar_bloqueo_cuota_v2()
                        break
                    _logger.warning(f"429 Ráfaga en paginación v2 (pág {params['numero_pagina']}). Reintentando en 5s...")
                    time.sleep(5)
                    retries_pag += 1
                    continue
                    
                response.raise_for_status()
                data = response.json()
                if data.get('success') != 'OK': break
                
                # Reseteamos retries si tuvimos éxito
                retries_pag = 0
                time.sleep(0.5) # Throttle
                
                payload = data.get('payload', {})
                items = payload.get('items', [])
                all_items.extend(items)
                
                paginacion = payload.get('paginacion', {})
                numero_actual = paginacion.get('numero_pagina', 1)
                total_paginas = paginacion.get('total_paginas', 1)
                
                if numero_actual >= total_paginas or numero_actual >= 50:
                    if numero_actual >= 50 and numero_actual < total_paginas:
                        _logger.warning(f"Límite de seguridad extremo alcanzado (50 páginas) para v2.")
                    break
                    
                params['numero_pagina'] += 1
        except Exception as e:
            _logger.error(f"Error v2 compras agiles: {e}")
        return all_items

    @api.model
    def get_compra_agil_details_v2(self, codigo, max_retries=3):
        ticket = self._get_api_ticket()
        url = f"https://api2.mercadopublico.cl/v2/compra-agil/{codigo}"
        for intento in range(max_retries + 1):
            try:
                if intento > 0: time.sleep(2 ** intento + random.uniform(0, 1))
                
                self._incrementar_consumo_api_v2()
                response = requests.get(url, headers={'ticket': ticket}, timeout=15)
                
                if response.status_code == 429:
                    if intento == max_retries:
                        self._marcar_bloqueo_cuota_v2()
                        return None
                    _logger.warning(f"429 Ráfaga en detalle v2 {codigo}. Reintentando en 5s...")
                    time.sleep(5)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                if data.get('success') != 'OK': return None
                
                time.sleep(0.5) # Throttle para evitar burst limit
                return data.get('payload')
            except Exception as e:
                _logger.warning(f"Error detalle v2 {codigo} (intento {intento}): {e}")
        return None

    # --- Sincronización y Procesamiento ---
    @api.model
    def importar_licitaciones(self):
        """Descarga listados de v1 y v2 según configuración y crea registros en estado 'nuevo'."""
        config = self._get_config()
        nuevas = 0
        existentes = 0
        
        # 1. Licitaciones (v1)
        chile_tz = pytz.timezone('America/Santiago')
        # Usar la hora de Chile para evitar que en UTC (madrugada) calcule el día de mañana
        fecha_actual_chile = datetime.now(pytz.utc).astimezone(chile_tz)

        if config.mercadopublico_sincronizar_licitaciones:
            fecha_v1 = (fecha_actual_chile - timedelta(days=config.mercadopublico_dias_busqueda_atras)).strftime('%d%m%Y')
            _logger.info(f"Iniciando sincronización v1 (Licitaciones) para la fecha: {fecha_v1} (hora Chile)")
            all_v1 = []
            if config.mercadopublico_filtro_organismo_favorito == 'filtrar_solo_favoritos':
                for org in config.mercadopublico_organismo_favorito_ids:
                    res = self.get_licitaciones_by_date_v1(fecha_v1, codigo_organismo=org.codigo)
                    all_v1.extend(res.get('Listado', []))
            else:
                res = self.get_licitaciones_by_date_v1(fecha_v1)
                all_v1 = res.get('Listado', []) if isinstance(res, dict) else []
            
            _logger.info(f"API v1 retornó {len(all_v1)} registros preliminares.")
            
            codigos_existentes_v1 = set(self.env['mercadopublico.licitacion'].search([('tipo_proceso', '=', 'licitacion')]).mapped('codigo'))
            procesados_v1 = set()
            for lic_data in all_v1:
                codigo = lic_data.get('CodigoExterno')
                if not codigo or codigo in procesados_v1: continue
                procesados_v1.add(codigo)

                if codigo in codigos_existentes_v1:
                    existentes += 1; continue
                self.env['mercadopublico.licitacion'].create({
                    'name': lic_data.get('Nombre', 'Sin nombre'),
                    'codigo': codigo,
                    'tipo_proceso': 'licitacion',
                    'comprador_nombre': lic_data.get('NombreOrganismo'),
                    'estado': self._map_estado_v1(lic_data.get('CodigoEstado')),
                    'state': 'nuevo',
                    'decision_filtro': 'pendiente'
                })
                nuevas += 1

        # 2. Compras Ágiles (v2)
        if config.mercadopublico_sincronizar_compra_agil:
            if config.mercadopublico_v2_bloqueado_hasta and fields.Datetime.now() < config.mercadopublico_v2_bloqueado_hasta:
                _logger.warning("Sincronización v2 omitida. Cuota bloqueada hasta: %s", config.mercadopublico_v2_bloqueado_hasta)
            else:
                dia_objetivo = fecha_actual_chile - timedelta(days=config.mercadopublico_dias_busqueda_atras)
                
                desde_str = dia_objetivo.strftime('%Y-%m-%dT00:00:00Z')
                hasta_str = dia_objetivo.strftime('%Y-%m-%dT23:59:59Z')
                
                _logger.info(f"Iniciando sincronización v2 (Compra Ágil) para UN SOLO DÍA: {desde_str[:10]}")
                
                # Como ahora es solo 1 día, descargaremos todas las páginas de ese día sin descartar nada.
                all_v2 = self.get_compras_agiles_v2(desde_str, hasta_str)
                _logger.info(f"API v2 retornó {len(all_v2)} registros preliminares.")
                
                codigos_existentes_v2 = set(self.env['mercadopublico.licitacion'].search([('tipo_proceso', '=', 'compra_agil')]).mapped('codigo'))
                procesados_v2 = set()
                for ca_data in all_v2:
                    codigo = ca_data.get('codigo')
                    if not codigo or codigo in procesados_v2: continue
                    procesados_v2.add(codigo)

                    if codigo in codigos_existentes_v2:
                        existentes += 1; continue
                    self.env['mercadopublico.licitacion'].create({
                        'name': ca_data.get('nombre', 'Sin nombre'),
                        'codigo': codigo,
                        'tipo_proceso': 'compra_agil',
                        'comprador_nombre': ca_data.get('institucion', {}).get('organismo_comprador', ''),
                        'estado': ca_data.get('estado', {}).get('codigo', 'publicada'),
                        'state': 'nuevo',
                        'decision_filtro': 'pendiente'
                    })
                    nuevas += 1

        _logger.info(f"Importación terminada. Nuevas: {nuevas}, Existentes: {existentes}")
        return {'nuevas': nuevas, 'existentes': existentes}

    @api.model
    def analizar_pendientes(self, limite=20):
        hace_15min = fields.Datetime.now() - timedelta(minutes=15)
        bloqueadas = self.env['mercadopublico.licitacion'].search([('state', '=', 'analizando'), ('write_date', '<', hace_15min)])
        if bloqueadas: bloqueadas.write({'state': 'nuevo'})

        licitaciones = self.env['mercadopublico.licitacion'].search([('state', '=', 'nuevo')], limit=limite)
        if not licitaciones: return 0

        _logger.info(f"Analizando lote de {len(licitaciones)} licitaciones pendientes.")
        licitaciones.write({'state': 'analizando'})

        # Cargar filtros: palabras clave activas y categorías configuradas en config
        config = self._get_config()
        keywords_activos = config.mercadopublico_filtro_keyword_ids.filtered(lambda f: f.active)
        cat_filtro_ids = set(config.mercadopublico_filtro_categoria_ids.ids)

        # Integración con Productos: Agregar categorías UNSPSC mapeadas a productos/categorías
        if 'product.template' in self.env:
            prod_cats = self.env['product.template'].search([]).mapped('todas_mercadopublico_categoria_ids')
            cat_filtro_ids.update(prod_cats.ids)

        hay_filtros = bool(keywords_activos) or bool(cat_filtro_ids)

        procesadas = 0
        for lic in licitaciones:
            try:
                full_data = None
                vals = {}
                categorias_extraidas = []
                texto_busqueda = ""

                if lic.tipo_proceso == 'licitacion':
                    full_data = self.get_licitacion_details_v1(lic.codigo)
                    if full_data:
                        vals = self._map_licitacion_fields_v1(full_data)
                        texto_busqueda = f"{vals.get('name', '')} {vals.get('descripcion', '')}".lower()
                        items_crear = []
                        for item in full_data.get('Items', {}).get('Listado', []) if isinstance(full_data.get('Items'), dict) else []:
                            if isinstance(item, dict):
                                if item.get('CodigoCategoria'):
                                    categorias_extraidas.append(str(item.get('CodigoCategoria')))
                                
                                items_crear.append((0, 0, {
                                    'codigo_producto': str(item.get('CodigoProducto', '')),
                                    'codigo_categoria': str(item.get('CodigoCategoria', '')),
                                    'name': item.get('NombreProducto', ''),
                                    'descripcion': item.get('Descripcion', ''),
                                    'cantidad': float(item.get('Cantidad', 0) or 0),
                                    'unidad_medida': item.get('UnidadMedida', '')
                                }))
                                texto_busqueda += f" {item.get('NombreProducto', '')} {item.get('Descripcion', '')}".lower()

                else:
                    if config.mercadopublico_v2_bloqueado_hasta and fields.Datetime.now() < config.mercadopublico_v2_bloqueado_hasta:
                        lic.write({'state': 'nuevo'})
                        continue
                    
                    full_data = self.get_compra_agil_details_v2(lic.codigo)
                    if full_data:
                        vals = self._map_compra_agil_fields_v2(full_data)
                        texto_busqueda = f"{vals.get('name', '')} {vals.get('descripcion', '')}".lower()
                        items_crear = []
                        for prod in full_data.get('productos_solicitados', []):
                            cod = str(prod.get('codigo_producto', ''))
                            if len(cod) == 8 and cod.isdigit(): categorias_extraidas.append(cod)

                            items_crear.append((0, 0, {
                                'codigo_producto': cod,
                                'codigo_categoria': cod if len(cod) == 8 and cod.isdigit() else '',
                                'name': prod.get('nombre', ''),
                                'descripcion': prod.get('descripcion', ''),
                                'cantidad': float(prod.get('cantidad', 0) or 0),
                                'unidad_medida': prod.get('unidad_medida', '')
                            }))
                            texto_busqueda += f" {prod.get('nombre', '')} {prod.get('descripcion', '')}".lower()

                if not full_data:
                    lic.write({'state': 'analizado', 'decision_filtro': 'no_apta', 'motivo_descarte': 'No se obtuvieron detalles de la API.'})
                    continue

                # Mapear categorías Odoo
                cats_odoo = self.env['mercadopublico.categoria']
                cat_ids = []
                if categorias_extraidas:
                    cats_odoo = self.env['mercadopublico.categoria'].search([('codigo', 'in', categorias_extraidas)])
                    cat_ids = cats_odoo.ids
                if cat_ids:
                    vals['categoria_ids'] = [(6, 0, cat_ids)]

                if items_crear:
                    for idx, (_, _, item_vals) in enumerate(items_crear):
                        item_text = f"{item_vals.get('name', '')} {item_vals.get('descripcion', '')}".lower()
                        item_match = False
                        
                        item_cat = item_vals.get('codigo_categoria')
                        if cat_filtro_ids and item_cat:
                            cat_record = cats_odoo.filtered(lambda c: c.codigo == item_cat)
                            if cat_record and cat_record.id in cat_filtro_ids:
                                item_match = True
                                
                        if not item_match:
                            if FUZZY_AVAILABLE:
                                for f in keywords_activos:
                                    if f.keyword and fuzz.partial_ratio(f.keyword.lower(), item_text) >= 90:
                                        item_match = True
                                        break
                            else:
                                for f in keywords_activos:
                                    if f.keyword and f.keyword.lower() in item_text:
                                        item_match = True
                                        break
                                        
                        items_crear[idx][2]['is_match'] = item_match
                        
                    vals['item_ids'] = [(5, 0, 0)] + items_crear

                # Filtrado simplificado (solo inclusión) con Rating
                es_apta = False
                motivo = ""
                puntuacion = 0
                motivos_list = []

                if not hay_filtros:
                    # Sin filtros configurados: todas son aptas por defecto
                    es_apta, motivo = True, "Sin filtros configurados, aceptada por defecto."
                    puntuacion = 1
                else:
                    # Verificar coincidencia por categoría o palabra clave (Base Apta = 1 Estrella)
                    if cat_filtro_ids and any(c_id in cat_filtro_ids for c_id in cat_ids):
                        cat_match = self.env['mercadopublico.categoria'].browse(
                            next(c_id for c_id in cat_ids if c_id in cat_filtro_ids)
                        )
                        puntuacion += 2
                        motivos_list.append(f"Categoría: [{cat_match.codigo}] {cat_match.name}")

                    if FUZZY_AVAILABLE:
                        for f in keywords_activos:
                            if f.keyword and fuzz.partial_ratio(f.keyword.lower(), texto_busqueda) >= 90:
                                puntuacion += 1
                                motivos_list.append(f"Palabra clave: {f.keyword}")
                                break
                    else:
                        for f in keywords_activos:
                            if f.keyword and f.keyword.lower() in texto_busqueda:
                                puntuacion += 1
                                motivos_list.append(f"Palabra clave (simple): {f.keyword}")
                                break

                    if puntuacion > 0:
                        es_apta = True
                    else:
                        motivo = "Sin coincidencias de categoría o palabra clave."

                # Filtros Secundarios (Solo si es Apta)
                if es_apta:
                    modo_ubic = config.mercadopublico_modo_ubicacion
                    ubicaciones_ids = config.mercadopublico_ubicacion_ids
                    
                    if modo_ubic != 'desactivado' and ubicaciones_ids:
                        comuna_api = (vals.get('comprador_comuna') or '').lower()
                        region_api = (vals.get('comprador_region') or '').lower()
                        match_ubic = any(u.name.lower() in comuna_api or u.name.lower() in region_api for u in ubicaciones_ids)
                        
                        if modo_ubic == 'excluyente' and not match_ubic:
                            es_apta = False
                            puntuacion = 0
                            motivos_list = ["EXCLUIDA: Ubicación no coincide"]
                        elif modo_ubic == 'aditivo' and match_ubic:
                            puntuacion += 1
                            motivos_list.append("Ubicación deseada")

                if es_apta:
                    modo_org = config.mercadopublico_filtro_organismo_favorito
                    if modo_org != 'desactivado':
                        org_codigo = vals.get('comprador_codigo', '')
                        org = self.env['mercadopublico.organismo'].search([('codigo', '=', org_codigo)], limit=1)
                        is_favorite = org.favorito if org else False
                        
                        if modo_org == 'excluyente' and not is_favorite:
                            es_apta = False
                            puntuacion = 0
                            motivos_list = ["EXCLUIDA: Organismo no favorito"]
                        elif modo_org == 'aditivo' and is_favorite:
                            puntuacion += 1
                            motivos_list.append("Organismo favorito")

                if es_apta:
                    motivo = " | ".join(motivos_list) if motivos_list else motivo

                vals['state'] = 'analizado'
                vals['decision_filtro'] = 'apta' if es_apta else 'no_apta'
                vals['palabras_clave_encontradas'] = motivo
                vals['rating'] = str(min(puntuacion, 3))

                if es_apta:
                    etapa_espera = self.env.ref('MercadoPublico-Odoo.etapa_en_espera', raise_if_not_found=False)
                    if etapa_espera: vals['etapa_id'] = etapa_espera.id
                else:
                    etapa_descartada = self.env.ref('MercadoPublico-Odoo.etapa_descartada', raise_if_not_found=False)
                    if etapa_descartada: vals['etapa_id'] = etapa_descartada.id

                lic.write(vals)
                if es_apta: self._notificar_hallazgo(lic)

                procesadas += 1
                time.sleep(0.3)

            except Exception as e:
                _logger.error(f"Error analizando {lic.codigo}: {e}")
                lic.write({'state': 'nuevo'})

        return procesadas

    def _notificar_hallazgo(self, lic):
        from markupsafe import Markup
        config = self._get_config()
        channel = config.mercadopublico_discuss_channel_id or self.env.ref('MercadoPublico-Odoo.channel_mercadopublico', raise_if_not_found=False)
        if not channel: return

        odoobot = self.env.ref('base.partner_root', raise_if_not_found=False)
        author_id = odoobot.id if odoobot else self.env.user.partner_id.id

        monto_fmt = "{:,.0f}".format(lic.monto_estimado).replace(",", ".")
        tipo_str = dict(self.env['mercadopublico.licitacion']._fields['tipo_proceso'].selection).get(lic.tipo_proceso)
        
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action = self.env.ref('MercadoPublico-Odoo.action_mercadopublico_licitacion', raise_if_not_found=False)
        action_id = action.id if action else ''
        odoo_url = f"{base_url}/odoo/action-{action_id}/{lic.id}" if action_id else f"{base_url}/odoo/mercadopublico.licitacion/{lic.id}"
        
        msg_html = f"""
            <div style="padding: 10px; border-left: 4px solid #714B67; margin-bottom: 10px;">
                <ul style="list-style-type: none; padding-left: 0; margin-bottom: 15px;">
                    <li style="margin-bottom: 4px;"><b>Tipo:</b> {tipo_str}</li>
                    <li style="margin-bottom: 4px;"><b>Nombre:</b> {lic.name}</li>
                    <li style="margin-bottom: 4px;"><b>Organismo:</b> {lic.comprador_nombre}</li>
                    <li style="margin-bottom: 4px;"><b>Monto Estimado:</b> {lic.moneda} {monto_fmt}</li>
                    <li style="margin-bottom: 4px;"><b>Motivo:</b> <span style="color: #28a745;">{lic.palabras_clave_encontradas}</span></li>
                </ul>
                <div style="display: flex; flex-direction: column; gap: 8px; max-width: 250px;">
                    <a href="{odoo_url}" target="_blank" style="display: block; text-decoration: none; padding: 6px 12px; background-color: #714B67; color: white; border-radius: 4px; text-align: center;">🔗 Ver en Odoo</a>
                    <a href="{lic.url_mercado_publico}" target="_blank" style="display: block; text-decoration: none; padding: 6px 12px; background-color: #007bff; color: white; border-radius: 4px; text-align: center;">🌐 Ver en Mercado Público</a>
                </div>
            </div>
        """
        channel.with_context(mail_create_nosubscribe=True).message_post(body=Markup(msg_html), message_type='comment', author_id=author_id)

    @api.model
    def cron_importar_licitaciones(self):
        self.importar_licitaciones()
        self.analizar_pendientes(limite=10)

    @api.model
    def cron_analizar_licitaciones(self):
        self.analizar_pendientes(limite=20)

    @api.model
    def sincronizar_organismos(self):
        ticket = self._get_api_ticket()
        url = "https://api.mercadopublico.cl/servicios/v1/Publico/Empresas/BuscarComprador"
        try:
            response = requests.get(url, params={"ticket": ticket}, timeout=30)
            data = response.json()
            codigos_org_existentes = set(self.env['mercadopublico.organismo'].search([]).mapped('codigo'))
            for org in data.get('listaEmpresas', []):
                codigo = org.get('CodigoEmpresa')
                if not codigo or codigo in codigos_org_existentes: continue
                self.env['mercadopublico.organismo'].create({'codigo': codigo, 'name': org.get('NombreEmpresa')})
        except Exception as e: _logger.error(f"Error sincronizando organismos: {e}")

    @api.model
    def _map_estado_v1(self, codigo_estado):
        mapping = {'5': 'publicada', '6': 'cerrada', '7': 'desierta', '8': 'adjudicada', '18': 'revocada', '19': 'suspendida'}
        return mapping.get(str(codigo_estado), 'publicada')

    @api.model
    def _map_licitacion_fields_v1(self, data):
        fechas, comprador = data.get('Fechas', {}), data.get('Comprador', {})
        return {
            'name': data.get('Nombre', 'Sin nombre'),
            'descripcion': data.get('Descripcion', ''),
            'comprador_codigo': comprador.get('CodigoOrganismo', ''),
            'comprador_nombre': comprador.get('NombreOrganismo', ''),
            'comprador_comuna': comprador.get('ComunaUnidad', ''),
            'comprador_region': comprador.get('RegionUnidad', ''),
            'fecha_publicacion': self._parse_fecha(fechas.get('FechaPublicacion')),
            'fecha_cierre': self._parse_fecha(fechas.get('FechaCierre')),
            'moneda': data.get('Moneda', ''),
            'monto_estimado': float(data.get('MontoEstimado', 0) or 0),
            'tipo_licitacion': data.get('Tipo', ''),
        }

    @api.model
    def _map_compra_agil_fields_v2(self, data):
        return {
            'name': data.get('nombre', 'Sin nombre'),
            'descripcion': data.get('descripcion', ''),
            'comprador_codigo': data.get('institucion', {}).get('rut', ''),
            'comprador_nombre': data.get('institucion', {}).get('organismo_comprador', ''),
            'comprador_region': data.get('institucion', {}).get('nombre_region', ''),
            'fecha_publicacion': self._parse_fecha(data.get('fechas', {}).get('fecha_publicacion')),
            'fecha_cierre': self._parse_fecha(data.get('fechas', {}).get('fecha_cierre')),
            'moneda': data.get('presupuesto', {}).get('moneda', ''),
            'monto_estimado': float(data.get('presupuesto', {}).get('monto_disponible_clp', 0) or 0),
        }

    @api.model
    def _parse_fecha(self, fecha_str):
        if not fecha_str: return False
        try: return datetime.fromisoformat(fecha_str.split('.')[0].replace('Z', ''))
        except (ValueError, AttributeError, TypeError): return False
