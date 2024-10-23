# -*- coding: utf-8 -*-
{
    'name': "web_module_extend",

    'summary': """web module changes.""",

    'description': """""",

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Web',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    # always loaded
    'data': [
        'report/external_layout_boxed_inherit.xml',


    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
