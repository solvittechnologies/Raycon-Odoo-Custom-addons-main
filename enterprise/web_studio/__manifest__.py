# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Studio",
    'description': """
Studio - Customize Odoo
=======================

This addon allows the user to customize most element of the user interface, in a
simple and graphical way. It has two main features:

* create a new application (add module, top level menu item, and default action)
* customize an existing application (edit menus, actions, views, translations, ...)

Note: Only the admin user is allowed to make those customizations.
""",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': [
        'base_action_rule',
        'base_import_module',
        'grid',
        'mail',
        'portal',
        'report',
        'web',
        'web_calendar',
        'web_editor',
        'web_gantt',
        'web_kanban',
    ],
    'data': [
        'views/web_studio_templates.xml',
        'views/actions.xml',
        'views/base_import_module_view.xml',
        'views/ir_actions_report_xml.xml',
        'views/ir_model.xml',
        'views/ir_model_data.xml',
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
    'application': True,
    'license': 'OEEL-1',
}
