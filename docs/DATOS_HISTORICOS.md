# Contexto: Análisis de Datos Históricos de Mercado Público

Este documento sirve como punto de partida para continuar el trabajo de análisis de datos históricos de Mercado Público (Tier 2). El objetivo es procesar, estructurar y disponibilizar metadatos de los últimos 2 años de licitaciones y órdenes de compra.

## 1. Estado Actual y Estructura

Se ha creado un proyecto de datos independiente del código fuente del módulo Odoo para manejar el gran volumen de información sin afectar el rendimiento de la aplicación principal.

**Ubicación:** `/home/butcherwutcher/Proyectos/dev/odoo-dev/odoo18/mercadopublico-data`

**Archivos Principales:**
- `scripts/download_historical.py`: Descarga automáticamente los archivos ZIP mensuales de "Datos Abiertos" de ChileCompra. Soporta un modo de prueba (1 mes) y un modo completo (24 meses usando el argumento `all`). Descarga de forma concurrente los datasets de Órdenes de Compra (`oc-da`) y Licitaciones (`lic-da`).
- `scripts/process_taxonomy_and_metadata.py`: Procesa en ráfagas (chunks) los archivos CSV descargados. Extrae la jerarquía de categorías UNSPSC (Segmento > Familia > Clase > Producto) de cadenas separadas por `/`, reconstruye los padres usando la lógica de los 8 dígitos, y agrega métricas clave (conteo de licitaciones/OC y sumatoria de montos en pesos chilenos).
- `data/raw/`: Directorio temporal donde se almacenan y descomprimen los archivos ZIP.
- `data/mercadopublico_categoria_data.xml`: Resultado XML de la jerarquía UNSPSC listo para ser importado o actualizado en Odoo.
- `data/metadata_categorias.json`: JSON con las métricas agregadas por cada categoría (ej. cuántas compras, montos transados totales).

## 2. Lo que ya se probó
Se ejecutó con éxito el pipeline para un (1) mes de prueba (Mayo de 2026), procesando más de 450,000 líneas entre OC y Licitaciones. El script extrajo exitosamente más de 1,700 categorías únicas, reconstruyó el árbol jerárquico y generó la metadata. La gestión de memoria es estable y funciona mediante lecturas iterativas en disco.

## 3. Tareas a Realizar (Tier 2)

El siguiente paso es ejecutar y consolidar el análisis de los 2 últimos años y construir la infraestructura para consumir esa data.

1. **Ejecución Histórica Masiva:**
   - Ejecutar el pipeline de descarga para los 24 meses (`python3 scripts/download_historical.py all`).
   - Ejecutar el procesamiento masivo. Dado el tamaño (estimado en millones de registros), revisar si `metadata_categorias.json` es suficiente o si es necesario migrar la persistencia de esta metadata a una base de datos local (ej: SQLite o DuckDB).

2. **Integración con el Módulo de Odoo:**
   - Diseñar la forma en que el módulo `MercadoPublico-Odoo` consultará esta metadata histórica.
   - *Opción A:* Importar los datos estadísticos directamente a Odoo mediante un modelo adicional (`mercadopublico.categoria.estadistica`) y vistas que permitan al usuario ver el valor de mercado de cada categoría.
   - *Opción B:* Exponer los datos mediante un pequeño servicio API en FastAPI/Flask corriendo en paralelo, al cual el módulo de Odoo hace peticiones bajo demanda.

3. **Enriquecimiento Adicional:**
   - Expandir el script `process_taxonomy_and_metadata.py` para extraer más insights, como estacionalidad (meses con más compras de una categoría específica) o distribución geográfica (regiones con más demanda por categoría).
