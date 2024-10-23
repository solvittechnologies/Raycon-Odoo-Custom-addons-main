# -*- coding: utf-8 -*-
{
    'name': "Human Resource",

    'summary': """Consolidate HR menus into a single HR module.""",

    'description': """""",

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resource',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr','hr_payroll', 'hr_expense', 'web_notify'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/mail_template.xml',
        #'templates.xml',
        'hr_menus.xml',
        'employee_inherit_view.xml',
        'hr_expense_inherit_view.xml',
        'hr_payroll_inherit_view.xml'

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
