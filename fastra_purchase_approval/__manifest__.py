# -*- coding: utf-8 -*-

{
    'name': 'Fastra Purchase Approvals',
    'version': '12.0.1.0.0',
    'summary': 'With this module you can approve purchase order in level wise.',
    'category': 'Purchases',
    'depends': ['purchase'],
    'data': [
        'data/ir_module_category_data.xml',

        'security/purchase_approve_level_security.xml',

        'views/purchase.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
