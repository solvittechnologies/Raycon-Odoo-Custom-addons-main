#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payslip aggregate rule',
    'category': 'Payroll',
    'sequence': 906,
    'summary': 'Allows to set salary rules as aggregate',
    'description': "Allows to set salary rules as aggregate",
    'images': ['static/images/main_thumb.png'],
    'author': 'João Jerónimo',
    
    'version': '1.0',
    
    # The license:
    'license': 'OPL-1',    # For Odoo10,11,12
    #'license': 'AGPL-3',    # For Odoo13
    
    'support': 'joao.jeronimo.pro@gmail.com',
    
    'application': False,
    'installable': True,
    'depends': [
        # For Odoo11 and Odoo12:
        'hr_payroll',                              # Odoo11 and 12
        
        # For Odoo13:
        #'hr_payroll_community',                     # Odoo13
        
        # Common dependencies:
    ],
    'data': [
        ## Compat views for easy porting between different Odoo versions:
        #'compat/compatviews11.xml',                # Odoo11
        'compat/compatviews12.xml',                # Odoo12
        #'compat/compatviews13.xml',                # Odoo13
        ## Version-dependent data files:
        'data/data12_n_11.xml',                    # Odoo 11 and 12
        #'data/data13.xml',                          # Odoo13
        
        # Common views:
        'views.xml',
    ],
    'demo': [
        'demo/demo12_n_11.xml',                    # Odoo 11 and 12
    ]
}
