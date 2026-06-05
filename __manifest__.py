# -*- coding: utf-8 -*-
{
    'name': 'Mercado Público Integration',
    'version': '18.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Professional integration with Chile Mercado Público. AI-powered tender discovery and CRM automation.',
    'description': """
Mercado Público Integration
================================

This module integrates the Chilean "Mercado Público" (ChileCompra) tender system with Odoo CRM.

Key Features:
-------------
* **Automated Sync**: Daily import of new public tenders (licitaciones) from Mercado Público API.
* **Smart Filtering**: Hybrid system (Fuzzy + Semantic Centroids) for high precision discovery.
* **Semantic Consensus**: Proportional averaging algorithm to eliminate redundancy bias.
* **CRM Automation**: Convert relevant tenders into CRM Leads or Opportunities with one click.
* **Tender Management**: Track the status of tenders (To Review, Converted, Discarded) directly in Odoo.
* **Discuss Integration**: Automatic notifications of relevant findings in Odoo channels.

Author: Tomás D. López (Kirulab SpA)
License: Proprietary
    """,
    'author': 'Kirulab SpA',
    'website': 'https://kirulab.tech',
    'depends': [
        'base',
        'crm',
        'sale',
        'project',
        'mail',
    ], 
    'data': [
        'security/mercadopublico_security.xml',
        'security/ir.model.access.csv',
        'data/mercadopublico_etapa_data.xml',
        'data/mercadopublico_categoria_data.xml',
        'data/ubicaciones_chile.xml',
        'data/cron_data.xml',
        'data/discuss_data.xml',
        'data/server_actions.xml',
        'wizards/mercadopublico_licitacion_descartar_wizard_view.xml',
        'wizards/mercadopublico_limpiar_wizard_view.xml',
        'wizards/mercadopublico_categoria_wizard_view.xml',
        'views/res_config_settings_views.xml',
        'views/mercadopublico_dashboard_view.xml',
        'views/mercadopublico_organismo_views.xml',
        'views/mercadopublico_categoria_views.xml',
        'views/mercadopublico_busqueda_view.xml',
        'views/mercadopublico_licitacion_views.xml',
        'views/mercadopublico_filtro_views.xml',
        'wizards/mercadopublico_onboarding_wizard_view.xml',
        'views/crm_lead_view.xml',
        'views/product_views.xml',
        'views/window_actions.xml',
        'views/actions_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'MercadoPublico-Odoo/static/src/js/categoria_tree_widget.js',
            'MercadoPublico-Odoo/static/src/xml/categoria_tree_widget.xml',
            'MercadoPublico-Odoo/static/src/css/categoria_tree_widget.css',
            'MercadoPublico-Odoo/static/src/js/ubicacion_tree_widget.js',
            'MercadoPublico-Odoo/static/src/xml/ubicacion_tree_widget.xml',
            'MercadoPublico-Odoo/static/src/css/ubicacion_tree_widget.css',
        ],
    },
    'external_dependencies': {
        'python': ['thefuzz'],
    },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'price': 0.0,
    'currency': 'EUR',
}
