# API Mercado Público Chile - Documentación Completa

Documentación consolidada de las tres principales APIs de la plataforma de compras públicas chilena para agentes de terminal y programación.

**Versión**: Mayo 2026  
**Estado**: Completo y actualizado  
**Plataforma**: ChileCompra - www.mercadopublico.cl

---

## ARCHIVOS INCLUIDOS

### 1. API-Compra-Agil-v2.md
Documentación completa de la API Compra Ágil v2 (versión más reciente y recomendada).

**Contenido**:
- Guía de primeros pasos y obtención de ticket
- Sistema de autenticación por token (header `ticket`)
- Control de cuota diaria (límite de solicitudes)
- 2 endpoints principales (listado y detalle)
- 7 grupos de parámetros de filtro (cambios, fechas, estado, región, búsqueda, paginación, orden)
- Diccionario completo de campos en listado, paginación y detalle
- Campos de productos solicitados y proveedores cotizando
- 6 ejemplos prácticos ejecutables (Python y cURL)
- Manejo exhaustivo de errores HTTP y código 429

**Tamaño**: ~35 KB | **Uso**: Monitoreo en tiempo real, sincronización incremental, búsquedas avanzadas

**URL Base**: `https://api2.mercadopublico.cl`

---

### 2. API-Licitaciones.md
Diccionario de datos de la API de Licitaciones (versión v1 - legacy).

**Contenido**:
- Estructura de respuesta XML/JSON/JSONP
- 97 campos documentados organizados por sección
- Comprador, fechas, estado, presupuesto, items, adjudicación
- 11 tipos de licitación clasificados por monto (L1, LE, LP, LQ, LR, E2, CO, B2, H2, I2, LS)
- 5 unidades monetarias (CLP, CLF, USD, UTM, EUR)
- 7 parámetros enumerados (estimación, modalidad pago, unidades tiempo, tipo acto administrativo)
- Clasificación de proveedores adjudicados por línea (item)

**Tamaño**: ~25 KB | **Uso**: Consulta de licitaciones, análisis de adjudicaciones, búsqueda de proveedores

**URL Base**: `http://api.mercadopublico.cl`

---

### 3. API-Ordenes-Compra.md
Diccionario de datos de la API de Órdenes de Compra (versión v1 - legacy).

**Contenido**:
- Estructura de respuesta XML/JSON/JSONP
- 74 campos documentados organizados por sección
- Información de comprador, proveedor, fechas, montos
- Detalles de items (productos) con precios y cantidades
- 2 tipos de orden de compra (SE, CM)
- 5 unidades monetarias equivalentes
- 7 códigos de tipo de despacho (envío, retiro, courier)
- 5 formas de pago predefinidas
- Estados de OC (enviada, aceptada, cancelada, recepción conforme, etc.)

**Tamaño**: ~22 KB | **Uso**: Tracking de órdenes, análisis de compras completadas, información de proveedores

**URL Base**: `http://api.mercadopublico.cl`

---

## GUÍA RÁPIDA POR CASO DE USO

### "Necesito monitorear nuevas Compras Ágiles en tiempo real"
→ **API-Compra-Agil-v2.md** → Sección "Primeros Pasos" → Ejemplo 1 (cambios últimas horas)

### "Quiero buscar licitaciones activas en mi región"
→ **API-Compra-Agil-v2.md** → Parámetro `region=` → Ejemplo 3 (búsqueda por palabras clave y región)

### "Necesito datos históricos de una licitación específica"
→ **API-Licitaciones.md** → Diccionario de campos (97 campos disponibles)

### "Debo obtener estado actual de una orden de compra"
→ **API-Ordenes-Compra.md** → Tabla de estados de OC → Campos de fechas y estado

### "Quiero sincronizar una base de datos local con cambios recientes"
→ **API-Compra-Agil-v2.md** → Ejemplo 2 (sincronización incremental) + Ejemplo 5 (paginación)

### "Necesito relacionar una Compra Ágil con su Orden de Compra emitida"
→ **API-Compra-Agil-v2.md** → Sección "Relación OC" + Ejemplo 6 (detección de OC)

### "Quiero acceder a detalles de productos adjudicados en una licitación"
→ **API-Licitaciones.md** → Campo 90-97 (Items y Adjudicación)

---

## AUTENTICACIÓN CONSOLIDADA

Todas las APIs requieren un `ticket` de acceso:

### Obtener Ticket

1. Ir a `https://www.chilecompra.cl/api/`
2. Click en "Pide tu ticket"
3. Iniciar sesión con Clave Única
4. Completar formulario
5. Recibir ticket por correo

### Usar Ticket

**Header HTTP requerido**:
```
ticket: TU_TICKET_AQUI
```

**cURL**:
```bash
curl -H "ticket: TU_TICKET_AQUI" "https://api2.mercadopublico.cl/v2/compra-agil"
```

**Python**:
```python
headers = {'ticket': 'TU_TICKET_AQUI'}
response = requests.get(url, headers=headers)
```

---

## CONTROL DE CUOTA (SOLO COMPRA ÁGIL v2)

- **Cuota diaria**: Por día calendario (no por 24 horas)
- **Reset**: Automático a las 00:00:01 cada nuevo día
- **Error 429**: Cuando se alcanza el límite
- **Recomendación**: Usar parámetro `ttl_cambio_ms` para sincronización incremental

---

## FORMATO DE RESPUESTA

### API Compra Ágil v2 (Recomendada)

**Exitosa**:
```json
{
  "success": "OK",
  "trace": null,
  "payload": { "items": [...], "paginacion": {...} },
  "errors": null
}
```

**Con error**:
```json
{
  "success": "NOK",
  "trace": null,
  "payload": null,
  "errors": [{ "codigo": "404", "mensaje": "...", "detalle": null }]
}
```

### APIs v1 (Licitaciones, OC)

Responden en XML/JSON/JSONP según parámetro `formato`:

```xml
<Licitaciones>
  <Cantidad>1</Cantidad>
  <FechaCreacion>2026-05-15T14:30:00</FechaCreacion>
  <Listado>
    <Licitacion>
      <!-- Campos aquí -->
    </Licitacion>
  </Listado>
</Licitaciones>
```

---

## CÓDIGOS DE ERROR HTTP COMUNES

| Código | Causa | Solución |
|--------|-------|----------|
| **400** | Parámetros inválidos | Revisar formato y rango de parámetros |
| **401** | Falta header `ticket` | Agregar header `ticket: TU_TICKET` |
| **403** | Ticket inválido/inactivo | Verificar ticket válido en ChileCompra |
| **404** | Código no existe | Verificar que código existe y es público |
| **429** | Cuota diaria agotada | Esperar hasta siguiente día calendario |
| **500** | Error servidor | Reintentar en unos minutos |
| **503** | Servicio no disponible | Esperar (mantenimiento) |

---

## AGENTES COMPATIBLES

Este conjunto de documentación está optimizado para uso por agentes de programación en terminal:

- **Claude Code** (Claude IDE): Acceso directo a estos MD como contexto
- **Gemini CLI**: Carga estos archivos como referencias
- **Antigravity**: Inyecta MD directamente en prompts de ejecución
- **Custom LLM Agents**: Parse de tablas y ejemplos código bien estructurados

**Características de diseño**:
- Tablas Markdown parseables
- Bloques de código con lenguaje especificado
- URLs directas sin especulación
- Nombres de campos exactos (copy-paste ready)
- Ejemplos ejecutables sin modificación

---

## MATRIZ DE COBERTURA

### Compra Ágil v2
| Aspecto | Cobertura |
|--------|----------|
| Autenticación | ✅ Completa |
| Endpoints | ✅ Ambos (listado y detalle) |
| Parámetros | ✅ Todos los 7 grupos |
| Campos | ✅ Listado, paginación, detalle, productos, proveedores |
| Ejemplos | ✅ 6 ejemplos (Python + cURL) |
| Manejo errores | ✅ Exhaustivo (429, cuota, etc.) |
| Estados | ✅ 6 estados documentados |

### Licitaciones v1
| Aspecto | Cobertura |
|--------|----------|
| Estructura | ✅ Completa |
| Campos | ✅ 97 campos documentados |
| Tipos licitación | ✅ 11 tipos clasificados |
| Parámetros enum | ✅ 7 parámetros |
| Ejemplos | ⚠️ Solo estructura API (no ejemplos de código) |

### Órdenes de Compra v1
| Aspecto | Cobertura |
|--------|----------|
| Estructura | ✅ Completa |
| Campos | ✅ 74 campos documentados |
| Tipos OC | ✅ 2 tipos |
| Parámetros enum | ✅ Despacho (7) y Pago (5) |
| Ejemplos | ✅ Ejemplo Python incluido |
| Estados OC | ✅ 7 estados documentados |

---

## NOTAS IMPORTANTES

### Limitaciones Conocidas

1. **Compra Ágil**: No tiene parámetro `codigo_organismo`. Usar `region=` como filtro primario.

2. **Compra Ágil**: Estado `oc_emitida` está definido pero no se usa en práctica. Usar `id_orden_compra != null` para detectar OC emitida.

3. **APIs v1** (Licitaciones, OC): Endpoints legacy. No tienen control de cuota explícito ni manejo de cambios incrementales.

### Recomendaciones de Uso

- **Preferir Compra Ágil v2** para nuevas integraciones (moderna, con cuota clara, cambios incrementales)
- **Usar Licitaciones** para datos históricos y análisis de adjudicaciones
- **Usar Órdenes de Compra** para tracking de adquisiciones completadas
- **Relacionar**: OC.CodigoLicitacion → Licitación OR Compra Ágil

---

## SOPORTE Y CONTACTO

- **Portal oficial**: https://www.mercadopublico.cl
- **Solicitar ticket**: https://www.chilecompra.cl/api/
- **Soporte ChileCompra**: Contacto en portal oficial

---

## CHANGELOG

| Versión | Fecha | Cambios |
|---------|-------|---------|
| **3.0** | Mayo 2026 | API Compra Ágil: correcciones de comportamiento real (oc_emitida, id_cotizacion, nuevo ejemplo 8.6) |
| **2.0** | Abril 2026 | Versión inicial API Compra Ágil v2 |
| **Beta** | — | APIs v1 (Licitaciones, OC) |

---

**Documentación preparada para agentes de terminal**  
**Última actualización**: Mayo 2026  
**Formato**: Markdown optimizado para parseo por LLM
