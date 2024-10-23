# -*- coding: utf-8 -*-
{
    'name': "Custom HelpDesk",
    'version': "1.1.1",
    'author': "kayode - BigFix",
    'category': "Tools",
    'summary': "A helpdesk system",
    'description': """
         Custom Helpdesk Bigfix
    """,
    'license':'LGPL-3',
    'data': [
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'views/helpdesk_tickets.xml',
        'views/helpdesk_team_views.xml',
        'views/helpdesk_stage_views.xml',
        'views/helpdesk_data.xml',
        'views/helpdesk_templates.xml',

    ],
    'depends': ['base', 'mail', 'portal','website'],
    'application': True,
}
