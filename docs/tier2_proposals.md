# Planificación Estratégica: Mercado Público Tier 2 (Versión Pagada)

Habiendo consolidado el Tier 1 (sincronización estable, filtros iniciales e integración nativa con CRM), el siguiente paso lógico es definir las características que compondrán la **versión PRO o Tier 2** del módulo. Estas características están diseñadas para justificar el modelo de pago, enfocándose en **ahorro extremo de tiempo (Automatización)** y **toma de decisiones estratégicas (Inteligencia de Negocios)**.

---

## 1. Clasificación Inteligente de Compras Ágiles (IA / LLM)

*   **El Problema:** La API v2 (Compra Ágil) de ChileCompra no entrega códigos UNSPSC precisos a nivel de ítem en la mayoría de los casos. Actualmente, usamos coincidencias de texto (fuzzy matching) que pueden tener falsos positivos o negativos.
*   **La Solución Tier 2:**
    *   Integrar un modelo de Inteligencia Artificial (ej. OpenAI, Claude, o un modelo local ligero).
    *   **Flujo propuesto:** Cada vez que entra una Compra Ágil nueva, el sistema envía los nombres y descripciones de los ítems a la IA junto con el catálogo de rubros (UNSPSC) de la empresa.
    *   **Resultado:** La IA devuelve con alta precisión si el negocio aplica o no, y es capaz de extraer marcas o modelos específicos solicitados en los textos libres.

## 2. Auto-Generación de Presupuestos (Sale Orders)

*   **El Problema:** Al convertir una licitación a Oportunidad, el vendedor tiene que leer los anexos, buscar los productos equivalentes en el ERP y armar la cotización manualmente.
*   **La Solución Tier 2:**
    *   Añadir un botón en la Oportunidad: **"Auto-Generar Cotización"**.
    *   **Flujo propuesto:** El sistema cruza los ítems extraídos de la licitación con el catálogo de productos (`product.product`) de Odoo.
    *   Si hay coincidencia exacta (SKU o código de barras), se añade la línea. Si no es exacta, se usa búsqueda semántica o IA para sugerir el producto más cercano del inventario.
    *   **Resultado:** El vendedor obtiene un borrador de Presupuesto (`sale.order`) ya armado con las cantidades solicitadas por el Estado, listo para ajustar precios (márgenes) y enviar.

## 3. Inteligencia Competitiva (Módulo de Adjudicaciones)

*   **El Problema:** Las empresas suelen operar a ciegas. No saben por qué pierden, a qué precio ganó la competencia, ni cuál es su verdadera cuota de mercado en Mercado Público.
*   **La Solución Tier 2:**
    *   Sincronizar el estado **"Adjudicada"** desde la API de ChileCompra.
    *   Crear nuevos modelos: `mercadopublico.adjudicacion` y `mercadopublico.competidor` (vinculado a `res.partner`).
    *   **Flujo propuesto:** Descargar automáticamente las actas de adjudicación de los rubros de interés. Registrar quién ganó, a qué precio y con qué productos exactamente.
    *   **Resultado:** Dashboards nativos en Odoo mostrando:
        *   **Win/Loss Ratio:** Estadísticas de victorias vs derrotas.
        *   **Market Share:** Gráficos mostrando qué porcentaje del rubro se llevan los principales competidores.
        *   **Price Tracking:** Historial de precios a los que la competencia vende ciertos productos al Estado.

## 4. Respuestas y Postulaciones (Bidding Kanban)

*   **El Problema:** Participar en una licitación requiere preparar múltiples documentos técnicos y administrativos, coordinar áreas y cumplir fechas inflexibles.
*   **La Solución Tier 2:**
    *   Integrar un Kanban especializado para el "Armado de Oferta" o vincularlo al módulo de Proyectos de Odoo.
    *   Al decidir participar, el sistema genera automáticamente un checklist de documentos requeridos (Boleta de Garantía, Anexos Técnicos, Formularios, etc.) asignando responsables y fechas límite obligatorias (estrictamente anteriores a la Fecha de Cierre).

## 5. Soporte Multi-Compañía Completo

*   **La Solución Tier 2:**
    *   Asegurar que el módulo maneje a la perfección entornos de Odoo con múltiples empresas (distintos RUTs bajo un mismo holding).
    *   Cada sucursal / empresa del ERP podrá tener su propio Ticket de API, sus propias categorías UNSPSC, reglas de filtrado y canales de notificación (Discuss), operando de manera totalmente aislada y segura en el mismo servidor Odoo.
