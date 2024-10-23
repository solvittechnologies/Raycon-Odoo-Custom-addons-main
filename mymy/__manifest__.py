# -*- coding: utf-8 -*-
{
    'name': "Mymy",

    'summary': "Mymy management",

    'description': """
        App to my knowledge of odoo.
    """,

    'author': "Hafeez",
    'category': 'Extra Tools',
    'version': '12.1.0',
    'application': True,
    'installable': True,

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'portal', 'web'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'assets.xml',
        'data/documents_data.xml',
        'views/documents_views.xml',
        'views/templates.xml',
        'wizard/request_activity_views.xml',
    ],

    'qweb': [
        "static/src/xml/*.xml",
    ],

    'demo': [
        'demo/demo.xml',
    ],
}

