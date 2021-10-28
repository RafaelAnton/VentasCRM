# -*- coding: utf-8 -*-
{
    'name': "Tipos de documento acorde a SUNAT",

    'summary': """
        """,

    'description': """
    """,

    'author': "ALTA BPO",
    'website': "http://www.altabpo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_pe', 'l10n_latam_base'],
    'external_dependencies': {
        'python': ['bs4'],
    },

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/l10n_latam_identification_type.xml',
        'data/ir_config_parameters.xml',
        'views/res_partner_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
