# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Fedex Shipping",
    'description': "Send your shippings through Fedex and track them online",
    'category': 'Warehouse',
    'version': '1.0',
    'depends': ['delivery', 'mail'],
    'data': [
        'data/delivery_fedex.xml',
        'views/delivery_fedex.xml',
    ],
    'license': 'OEEL-1',
    'uninstall_hook': 'uninstall_hook',
}
