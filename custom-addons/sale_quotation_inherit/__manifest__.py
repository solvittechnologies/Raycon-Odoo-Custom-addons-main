# -*- coding: utf-8 -*-
{
    'name': "Quatation Changes",

    'summary': """Customizing quotation for tds.""",

    'description': """""",

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'purchase', 'account', 'stock','mail', 'sale_crm', 'crm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        #'templates.xml',
        'views.xml',
        'res_partner_inherit_view.xml',
        'account_invoice_views.xml',
        'vendor_bill_view.xml',
        'purchase_order_view.xml',
        'product_inherit_view.xml',
        'crm_lead_inherit_view.xml',
        'report/report_template.xml',
        'report/report.xml'

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
