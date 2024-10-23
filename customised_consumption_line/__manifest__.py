# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Consumption Request Customised',
    'version' : '12.0.1.0.0',
    'summary': 'App for making Consumption request customisation',
    'sequence': -11,
    'description': """App for making Consumption request customisation""",
    'category': 'Inventory',
    'depends' : ['base','stock','od_material_consumption'],
    'data': [
        'views/stock_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}