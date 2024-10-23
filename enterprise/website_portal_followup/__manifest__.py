# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Website Followup',
    'category': 'Accounting',
    'complexity': 'easy',
    'description': """
This module adds a followup menu and features to your portal if followup and portal are installed.
==================================================================================================
    """,
    'depends': ['account_reports', 'website_portal', 'website'],
    'data': [
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo_invoices.yml',
    ],
    'installable': True,
    'license': 'OEEL-1',
}
