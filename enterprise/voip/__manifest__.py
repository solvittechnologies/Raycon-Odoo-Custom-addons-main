# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "VOIP Core",

    'summary': """
        Technical core for all the modules using the VOIP system.""",

    'description': """
        Technical core for all the modules using the VOIP system. 
        Contains the library needed in order to make the VOIP usable by other modules.
    """,

    'price': 399,
    'currency': 'EUR',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Hidden',
    'version': '1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'sales_team'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/voip_templates.xml',
        'views/res_users_views.xml',
    ],
    'js': ['static/src/js/*.js'],
    'css': ['static/src/css/*.css'],
    'qweb': ['static/src/xml/*.xml'],
    'application' : False,
    'license': 'OEEL-1',
}