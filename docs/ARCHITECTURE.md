# Documento de Arquitectura: Mercado Público Odoo (Versión 18+)

## 1. Objetivo del Proyecto
Profesionalizar el módulo de integración con la API de Mercado Público para Odoo 18. El sistema actúa como un **Filtro Inteligente**, importando licitaciones masivamente y seleccionando solo aquellas relevantes mediante IA.

## 2. Flujo de Trabajo (2 Pasos)

### Paso 1: Importación Rápida
*   El sistema descarga el listado básico de licitaciones del día desde la API oficial.
*   Crea registros en el modelo `mercadopublico.licitacion` en estado `nuevo`.
*   Este paso es extremadamente rápido y no bloquea el servidor.

### Paso 2: Análisis en Lotes (Batch Analysis)
*   Un proceso en segundo plano (Cron) o manual toma las licitaciones en estado `nuevo`.
*   **Filtrado Primario:** Se aplica Fuzzy Matching o Similitud Semántica (Vectores) según la configuración.
*   **Auditoría LLM (Opcional):** Si el filtro primario es superado, Gemini analiza el contexto para una decisión final.
*   **Clasificación:** Las licitaciones se marcan como `Apta` o `No Apta`.

## 3. Gestión de Oportunidades
*   **Kanban de 2 Columnas:** Las licitaciones `aptas` aparecen en "En Espera".
*   **Conversión CRM:** Al arrastrar a "Convertidas" o pulsar el botón, se crea automáticamente un Lead en Odoo CRM con toda la información vinculada.

## 4. Mantenimiento y Rendimiento
*   **Política de Retención:** El sistema elimina automáticamente las licitaciones `no_aptas` después de un periodo configurable (ej. 30 días).
*   **Dashboard Operativo:** Centro de control para monitorear KPIs, salud de las APIs y ejecutar acciones manuales.

## 5. Tecnologías Clave
*   **FuzzyWuzzy:** Para filtrado por palabras clave aproximadas.
*   **Google Gemini API:** Para embeddings semánticos y auditoría contextual de licitaciones.
*   **Sentence-Transformers (Opcional):** Para análisis semántico local si el hardware lo permite.
