# Plan de Refactorización: MercadoPublico-Odoo

**Fecha:** Junio 2026  
**Estado:** Planificación aprobada

---

## Contexto y motivación

El módulo actual usa dos estrategias de filtrado que no funcionan bien en la práctica:

1. **Transformer local (sentence-transformers):** rendimiento insuficiente para el hardware objetivo, dependencia pesada, resultados inconsistentes.
2. **Análisis semántico por embeddings con clustering:** complejidad arquitectónica alta para el beneficio obtenido. El modelo de clusters/centroides introduce deuda técnica significativa sin ventaja clara sobre filtrado por categorías estructuradas.

La refactorización reemplaza ambas estrategias por un enfoque basado en la taxonomía UNSPSC que ya existe en los datos de la API, combinado con FuzzyWuzzy para coincidencias de keywords. Se introduce también la integración con la API de Compra Ágil v2.

---

## Lo que se elimina

### Motor de embeddings local
El subsistema completo de vectorización local desaparece: el servicio de embeddings, la caché de vectores, y el modelo de clustering de filtros (centroides). Esto incluye las dependencias `sentence-transformers` y `numpy`.

### Motor semántico basado en clusters
El modelo `mercadopublico.cluster` y toda la lógica de agrupamiento de filtros por similitud semántica se eliminan. Era el componente más complejo y menos predecible del sistema.

### Lógica de bonus/malus
El mecanismo de ajuste de score por presencia/ausencia de keywords sobre el score semántico desaparece junto con el motor que lo necesitaba.

### Modo de procesamiento semántico
El campo `modo_procesamiento` pierde las opciones `semantic` y `llm_audit`. Solo queda el modo base, ahora reformulado como Tier 1. La auditoría LLM pasa a ser exclusiva del Tier 2 (Enterprise).

### Gemini API (en el módulo base)
La integración con Gemini se desacopla del módulo base y pasa al módulo Enterprise. El módulo base no tendrá dependencias externas de IA.

---

## Lo que se mantiene

### FuzzyWuzzy para keywords
Se conserva el matching aproximado (`fuzz.partial_ratio`) como método de búsqueda de keywords. Es ligero, predecible y sin dependencias pesadas. La diferencia con el estado actual es que deja de ser un componente auxiliar con bonus/malus y pasa a ser uno de los dos mecanismos principales de filtrado del Tier 1.

### Flujo de dos pasos (importación + análisis)
La separación entre importación rápida del listado y análisis posterior por lotes se mantiene. Es una buena arquitectura independientemente del algoritmo de filtrado.

### Integración CRM
La conversión de licitaciones aptas a Leads/Oportunidades en Odoo CRM no cambia.

### Notificaciones por canal de Discuss
El bot de notificaciones se mantiene sin cambios.

### Gestión de organismos favoritos
El modelo `mercadopublico.organismo` y el filtro por organismos favoritos se mantienen.

---

## Lo que se añade

### Modelo de categorías UNSPSC

Se introduce `mercadopublico.categoria` para representar la taxonomía UNSPSC v7 que Mercado Público usa en todos sus procesos (licitaciones y órdenes de compra).

UNSPSC es jerárquica con cuatro niveles:

```
Segmento (2 dígitos)
  └── Familia (4 dígitos)
        └── Clase (6 dígitos)
              └── Producto/Commodity (8 dígitos)
```

El campo `Categoria` de la API ya contiene la ruta jerárquica completa en texto. El `CodigoCategoria` es el código numérico de ese nodo.

Las categorías se obtienen de dos fuentes:
- **Catálogo semilla**: generado a partir de los datos abiertos históricos (ZIPs mensuales de `transparenciachc.blob.core.windows.net`), cubre 2+ años de licitaciones reales. Se distribuye con el módulo como datos iniciales.
- **Captura incremental**: cada vez que se obtiene el detalle de una licitación nueva, sus categorías de Items se añaden al catálogo si no existen.

### Categorías en licitaciones

`mercadopublico.licitacion` añade una relación M2M con `mercadopublico.categoria`. Al procesar el detalle de una licitación se extraen los Items y se vinculan sus categorías al registro.

### Filtrado por categorías en los filtros

`mercadopublico.filtro` añade la posibilidad de seleccionar categorías UNSPSC como criterio de inclusión o exclusión. El usuario puede seleccionar a nivel de Segmento (amplio), Familia, Clase o Producto (específico), y la coincidencia se propaga hacia abajo en la jerarquía.

### Integración con API Compra Ágil v2

Se añade soporte para el endpoint `https://api2.mercadopublico.cl/v2/compra-agil`. Esta API más moderna permite:
- Filtrado por región, estado y palabras clave directamente en el query
- Sincronización incremental por timestamp (`ttl_cambio_ms` o rango de fechas)
- Paginación estructurada

Los procesos de Compra Ágil se almacenan en el mismo modelo `mercadopublico.licitacion` con un campo `tipo_proceso` que distingue entre `licitacion` (API v1) y `compra_agil` (API v2).

---

## Nueva lógica de filtrado (Tier 1)

El algoritmo de filtrado pasa a ser determinista y auditable:

```
Para cada licitación en estado "nuevo":
  1. Obtener detalle completo de la API
  2. Extraer categorías UNSPSC de los Items
  3. Verificar exclusiones primero:
     - ¿Alguna keyword de exclusión (fuzzy) aparece en nombre/descripción? → no_apta
     - ¿Alguna categoría del proceso está en la lista de exclusión? → no_apta
  4. Si pasa exclusiones, verificar inclusiones:
     - ¿Alguna keyword de inclusión (fuzzy) aparece en nombre/descripción? → apta
     - ¿Alguna categoría del proceso está en la lista de inclusión? → apta
  5. Si no hay match en inclusiones → no_apta
```

La decisión final es binaria y explicable: el sistema registra qué keyword o qué categoría activó la decisión.

---

## Separación en dos módulos

### Módulo base (Tier 1) — Community

Nombre de módulo actual conservado o renombrado. Sin dependencias de IA externas. Funciona con cualquier instalación de Odoo 18 Community o Enterprise.

**Dependencias Python:** `requests`, `fuzzywuzzy`  
**Dependencias Odoo:** `crm`, `mail`

### Módulo Enterprise (Tier 2) — pendiente

Módulo separado que extiende el base. Añade:
- Integración Gemini / Claude API para scoring contextual
- Análisis semántico de descripción completa
- Dashboard analytics avanzado
- (desarrollo posterior, cuando se tenga entorno Community estable)

---

## Proceso de extracción de categorías desde datos abiertos

Antes de publicar el módulo, se ejecuta un script one-shot (fuera de Odoo) que:

1. Descarga los ZIPs mensuales de licitaciones de los últimos 2-3 años desde el portal de datos abiertos de ChileCompra
2. Extrae todos los pares únicos `CodigoCategoria / Categoria`
3. Construye el árbol UNSPSC respetando la jerarquía (parseando la ruta del campo `Categoria`)
4. Genera un archivo de datos (`data/mercadopublico_categoria_data.xml`) que se carga automáticamente al instalar el módulo

Esto garantiza que el usuario tenga un catálogo de categorías útil desde el día 1, sin necesidad de procesar licitaciones históricas dentro de Odoo.

**URLs de datos abiertos:**
- Órdenes de Compra: `https://transparenciachc.blob.core.windows.net/oc-da/YYYY-M.zip`
- Licitaciones: `https://transparenciachc.blob.core.windows.net/lic-da/YYYY-M.zip`

El mes se expresa sin cero inicial (ej: `2026-1.zip` para enero 2026).

---

## Impacto en configuración de usuario

| Configuración actual | Estado tras refactorización |
|---|---|
| Modo de procesamiento: Base | Se mantiene (renombrado a Tier 1) |
| Modo de procesamiento: Semántico | Eliminado |
| Modo de procesamiento: Auditoría LLM | Pasa a Tier 2 |
| Motor de embeddings | Eliminado |
| Umbrales de similitud semántica | Eliminados |
| Palabras clave (keyword) | Se mantienen, usan FuzzyWuzzy |
| Palabras clave (concept) | Eliminadas |
| Clusters de filtros | Eliminados |
| Filtro por organismo favorito | Se mantiene |
| Filtro por categoría UNSPSC | **Nuevo** |

Los registros de licitaciones existentes no se pierden. Los campos de embedding/similarity quedan como `NULL` y se eliminan en la migración.
