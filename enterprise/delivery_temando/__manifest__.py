# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Temando Shipping",
    'description': "Send your shippings through Temando and track them online",
    'category': 'Warehouse',
    'version': '1.0',
    'depends': ['delivery', 'mail'],
    'data': [
        'data/delivery_temando.xml',
        'data/delivery.carrier.csv',
        'views/delivery_temando_view.xml',
        'views/sale_order_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_warehouse_view.xml',
    ],
    'demo': [
        'data/delivery_temando_demo.xml',
    ],
    'license': 'OEEL-1',
    'uninstall_hook': 'uninstall_hook',
}
