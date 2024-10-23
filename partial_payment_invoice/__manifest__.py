# -*- coding: utf-8 -*-
{
    'name': 'Partial Payment Invoice',
    'summary': 'Partial Payment Invoice',
    'category': '',
    'version': '12.0',
    'depends': [
        'account','payment'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/partial_payment_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
