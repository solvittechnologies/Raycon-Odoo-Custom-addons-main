#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payslip Batch Report',
    'category': 'Payroll',
    'sequence': 906,
    'summary': 'Summary of all payslips as a pivot table',
    'description': "Create Payroll reports based on pivot view engine.",
    'images': ['static/images/main_thumb.png'],
    'author': 'João Jerónimo',
    
    'version': '1.0',

    'currency': 'EUR',
    
    # The license:
    'license': 'LGPL-3',    # For Odoo10,11,12
    #'license': 'AGPL-3',    # For Odoo13
    
    'support': 'joao.jeronimo.pro@gmail.com',
    
    'application': False,
    'installable': True,
    'depends': [
        'payslip_aggregate_rule',
    ],
    'data': [
        'views/pivot_views.xml',
        'views/payslip_run_views.xml',
        'views/menus.xml',
    ],
}
