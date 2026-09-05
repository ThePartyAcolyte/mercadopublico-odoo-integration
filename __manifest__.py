# -*- coding: utf-8 -*-
{
    'name': 'Mercado Público Integration',
    'version': '18.0.1.0.2',
    'category': 'Sales/CRM',
    'summary': 'Fetch, filter, and convert public tenders into CRM opportunities',
    'description': """
Mercado Público Integration
================================

This module integrates the Chilean "Mercado Público" (ChileCompra) tender system with Odoo CRM.

Key Features:
-------------
* **Automated Sync**: Import of public tenders (licitaciones) and Compras Ágiles from Mercado Público API.
* **Smart Filtering**: Precision filtering using keywords, UNSPSC categories, and fuzzy matching.
* **CRM Automation**: Convert relevant tenders into CRM Leads or Opportunities with one click.
* **Tender Management**: Track tender status (To Review, Converted, Discarded) directly in Odoo.
* **Discuss Integration**: Automatic notifications of relevant findings in Odoo channels.
    """,
    'author': 'ThePartyAcolyte',
    'website': 'https://github.com/ThePartyAcolyte/odoo-public-apps',
    'depends': [
        'base',
        'crm',
        'mail',
    ],
    'data': [
        'security/mercadopublico_security.xml',
        'security/ir.model.access.csv',
        'data/mercadopublico_stage_data.xml',
        'data/mercadopublico_category_data.xml',
        'data/ubicaciones_chile.xml',
        'data/cron_data.xml',
        'data/discuss_data.xml',
        'data/server_actions.xml',
        'wizards/mercadopublico_tender_discard_wizard_view.xml',
        'wizards/mercadopublico_clear_wizard_view.xml',
        'wizards/mercadopublico_category_wizard_view.xml',
        'views/res_config_settings_views.xml',
        'views/mercadopublico_dashboard_view.xml',
        'views/mercadopublico_buyer_views.xml',
        'views/mercadopublico_category_views.xml',
        'views/mercadopublico_search_views.xml',
        'views/mercadopublico_tender_views.xml',
        'views/mercadopublico_keyword_views.xml',
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
        'static/description/hero_dashboard.png',
        'static/description/screenshot-01.png',
        'static/description/screenshot-02.png',
        'static/description/screenshot-03.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'price': 0.0,
    'currency': 'EUR',
}
