# -*- coding: utf-8 -*-

{
    'name': 'Fastra Licence',
    'version': '12.0.1.0.0',
    'summary': 'With this module you can make database to expire',
    'category': 'Hidden',
    'depends': ['web'],
    'data': [
        'data/ir_config_parameter.xml',
        'views/assets.xml',
    ],
    'qweb': [
        "static/src/xml/template.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
