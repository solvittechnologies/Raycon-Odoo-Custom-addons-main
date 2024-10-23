# -*- coding: utf-8 -*-
{
    'name': "Firebase Cloud Messaging",
    'version': "1.0",
    'summary': 'Push notification for mobile app',
    'description': """
Google Firebase Messaging Integration
=====================================
This module allows to send FCM push notification on registered mobiles
for every message in chatter.

**Configure your API keys from General Setting**
    """,
    'depends': ['mail', 'web_mobile'],
    'data': [
        'views/assets.xml',
        'views/res_config.xml',
        'views/res_partner.xml',
        'security/ir.model.access.csv',
        'security/mail_push_security.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
