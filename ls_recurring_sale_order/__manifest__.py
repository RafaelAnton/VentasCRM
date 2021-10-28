# -*- coding: utf-8 -*-
{
    'name': "Recurring Sale Order",
    'category': 'Sale',
    'summary': 'Create and manage recurring sale order',
    'version': '1.0',
    'license': 'LGPL-3',
    'author': "Linescripts Softwares",
    'support': 'support@linescripts.com',
    'website': "https://www.linescripts.com",
    'description': 'Create and manage recurring sale order',
    'depends': ['sale_management', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/ls_sale_order.xml',
        'views/ls_recurring_order.xml',
        'views/ls_res_config_settings.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'price': 0.00,
    'currency': 'EUR',
    'installable': True,
    'application': True,

}
