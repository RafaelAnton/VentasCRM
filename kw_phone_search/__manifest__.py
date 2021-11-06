{
    'name': 'Advanced contact search by name email and phone',

    'author': 'Kitworks Systems',
    'website': 'https://kitworks.systems/',

    'category': 'Extra Tools',
    'license': 'OPL-1',
    'version': '14.0.0.0.2',

    'depends': [
        'phone_validation', 'kw_mixin', 'kw_phone',
    ],
    'data': [
        'views/partner_view.xml',
        'views/res_config_settings_view.xml',
    ],
    'installable': True,

    'images': [
        'static/description/cover.png',
        'static/description/icon.png',
    ],

}
