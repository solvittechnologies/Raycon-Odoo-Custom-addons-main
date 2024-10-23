# -*- coding: utf-8 -*-
{
    'name': 'Fastra Inventory - Simbeez',
    'summary': 'Fastra Inventory - Simbeez',
    'category': 'Warehouse',
    'version': '12.0',
    'author': 'Simbeez',
    'depends': [
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/request_inventory.xml',
        'wizard/inventory_request_confirm_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
