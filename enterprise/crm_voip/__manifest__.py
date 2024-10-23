# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Odoo VOIP",

    'summary': """
        Automate calls transfers, logs and emails""",

    'description': """
        Long description of module's purpose
    """,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['voip','base','crm','web_enterprise'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/crm_phonecall_log_wizard_views.xml',
        'wizard/crm_phonecall_schedule_wizard_views.xml',
        'wizard/crm_phonecall_transfer_wizard_views.xml',
        'views/crm_voip_templates.xml',
        'views/crm_phonecall_views.xml',
        'views/crm_lead_views.xml',
        'views/res_config_views.xml',
        'views/res_partner_views.xml',
        'views/crm_phonecall_report_views.xml',
        'data/mail_template_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'js': ['static/src/js/*.js'],
    'css': ['static/src/css/*.css'],
    'qweb': ['static/src/xml/*.xml'],
    'images': ['static/description/voip.png'],
    'application' : True,
    'license': 'OEEL-1',
}