# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Website Helpdesk',
    'category': 'Hidden',
    'sequence': 57,
    'summary': 'Bridge module for helpdesk modules using the website.',
    'description': 'Bridge module for helpdesk modules using the website.',
    'depends': [
        'website_form_editor',
        'helpdesk',
        'website_portal'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/helpdesk_security.xml',
        'views/helpdesk_templates.xml',
        'views/helpdesk_views.xml'
    ],
    'license': 'OEEL-1',
}
