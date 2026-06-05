# Odoo Mercado Público Integration

Este módulo integra tu ERP Odoo con el portal de compras gubernamentales de Chile (ChileCompra / Mercado Público), permitiéndote automatizar la búsqueda de negocios y enfocar tus esfuerzos en vender.

## Características Principales (Tier 1)

* 🚀 **Sincronización Automática:** Descarga automáticamente y de forma periódica las nuevas Licitaciones Públicas y procesos de Compra Ágil directamente a tu Odoo.
* 🎯 **Filtros Inteligentes (UNSPSC y Palabras Clave):** Define tus rubros comerciales (códigos UNSPSC) y palabras clave de negocio. El módulo evalúa cada licitación, descartando el ruido y destacando únicamente los negocios aptos para tu empresa.
* 🔗 **Integración Nativa con CRM:** Convierte cualquier licitación interesante en una Oportunidad de Odoo con un solo clic. Las oportunidades se asignarán automáticamente a tu Equipo de Ventas y Vendedor configurado.
* 🔔 **Notificaciones Inmediatas:** Se integra con Odoo Discuss para enviarte un mensaje automático en un canal dedicado cada vez que el sistema detecte una nueva oportunidad apta.
* 🧹 **Mantenimiento Autónomo:** El sistema incluye tareas programadas que archivan licitaciones expiradas y eliminan aquellas descartadas después de cierta cantidad de días, manteniendo tu base de datos limpia y rápida.

## Configuración Inicial (Onboarding)

Al instalar el módulo, serás guiado por un Wizard de Configuración Inicial donde podrás:
1. Conectar tu **Ticket de la API** (gratuito en api.mercadopublico.cl).
2. Definir qué procesos sincronizar (Licitaciones, Compras Ágiles o ambos).
3. Establecer tus **Categorías UNSPSC** y **Palabras Clave**.
4. Configurar tu equipo y responsable en el **CRM**.

También puedes editar estos parámetros más tarde desde `Ajustes > Mercado Público`.

## Soporte y Recursos

* Si necesitas ayuda, visita nuestro manual de configuración y soporte en: [kirulab.tech/productos/mercadopublico](https://kirulab.tech/productos/mercadopublico)

## Compatibilidad

Odoo 18.0.
