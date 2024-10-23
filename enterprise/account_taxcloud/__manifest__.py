# -*- coding: utf-8 -*-
{
    'name': "Account TaxCloud",
    'summary': """TaxCloud make it easy for business to comply with sales tax law""",
    'description': """
        Compute sales tax automatically using TaxCloud based on customer address in United States.
    """,
    'website': "https://www.odoo.com",
    'category': 'Accounting &amp; Finance',
    'version': '1.0',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_fiscal_position_view.xml',
        'views/account_invoice_views.xml',
        'views/product_view.xml',
        'views/res_config_view.xml',
        'data/account_taxcloud_data.xml',
    ],
    'license': 'OEEL-1',
}
