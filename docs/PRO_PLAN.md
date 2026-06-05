# Plan de Expansión: Mercado Público PRO

Este documento detalla la visión para la versión avanzada del módulo, concebida como una herramienta de análisis de viabilidad técnica y financiera profunda para empresas licitadoras.

## 1. Visión del Producto
Transformar la búsqueda de licitaciones de un proceso de "descubrimiento" a un proceso de "toma de decisiones estratégica" mediante el uso de agentes de IA especializados.

## 2. Características Premium (PRO)

### A. Análisis de Viabilidad Profunda (Deep Tech Analysis)
*   **Lectura de Bases (RAG):** Extracción y resumen de requisitos técnicos, administrativos y económicos desde archivos PDF/DOCX adjuntos usando embeddings y LLMs.
*   **Business Matching:** Comparar los requisitos de la licitación con el perfil de la empresa (Capacidad financiera, experiencia previa, equipo disponible).
*   **Análisis de Riesgos:** Identificación automática de cláusulas punitivas, plazos agresivos o requisitos de capital difíciles de cumplir.

### B. Enriquecimiento mediante Web Scraping
*   **Extracción de Ficha Web:** Obtener datos que no viajan por la API oficial (ej: preguntas y respuestas del foro, historial de modificaciones de bases).
*   **Inteligencia de Competencia:** Analizar quiénes han ganado licitaciones similares en el pasado mediante scraping de actas de adjudicación e historial de oferentes.

### C. Integración Avanzada Odoo
*   **Módulo de Proyectos:** Creación automática de un Proyecto de Odoo con tareas basadas en los hitos de la licitación (ej: "Entrega de boleta de garantía", "Subida de oferta técnica").
*   **Módulo de Compras/Costos:** Estimación de margen basada en los precios de catálogo de Odoo vs el presupuesto estimado de la licitación.

### D. Agentes de IA Multi-Modelo
*   **Orquestador:** Uso de modelos más potentes (GPT-4o, Claude 3.5 Sonnet) para el análisis final de documentos complejos.
*   **Chat con la Licitación:** Un widget de chat en la oportunidad de CRM que permite preguntar: "¿Cuáles son las multas por retraso en esta licitación?" basándose en los documentos leídos.

## 3. Arquitectura Técnica (Módulo Separado)
*   **Repositorio:** `mercadopublico-odoo-pro` (Repositorio privado/pago).
*   **Dependencia:** Requiere el módulo base `mercadopublico-odoo`.
*   **Tecnologías:** `Playwright` o `BeautifulSoup` para scraping, `LangChain` o `LlamaIndex` para RAG (Retrieval-Augmented Generation).
