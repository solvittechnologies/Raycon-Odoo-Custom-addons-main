# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Manufacturing Barcode Scanning',
    'version': '1.0',
    'website': 'https://www.odoo.com/page/manufacturing',
    'category': 'Manufacturing',
    'summary': 'Add barcode scanning facilities to manufacturing',
    'depends': ['mrp_workorder', 'stock_barcode'],
    'description': """This module adds support for barcodes scanning to the manufacturing system.""",
    'data': [
        'views/inherited_mrp_production_views.xml',
        'views/inherited_mrp_workorder_views.xml',
        'views/inherited_stock_move_views.xml',
        'views/inherited_mrp_workcenter_block_view.xml',
        'views/inherited_picking_type_views.xml',
        'views/mrp_barcode_templates.xml',
    ],
    'qweb': [
        "static/src/xml/mrp_barcode.xml",
    ],
    'demo': [
        'data/mrp_barcode_demo.xml',
    ],
    'license': 'OEEL-1',
}
