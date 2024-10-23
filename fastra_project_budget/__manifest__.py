# -*- coding: utf-8 -*-

{
    'name': 'Project Analysis Extends',
    'version': '12.0.1.0.0',
    'summary': 'Project Analysis Extends',
    'depends': ['project_analysis_auslind', 'kay_petty_cash', 'purchase_request_petty_cash'],
    'data': [
        'data/ir_module_category_data.xml',

        'security/ir.model.access.csv',
        'security/project_budget_security.xml',

        'views/fastra_project_analysis_budget.xml',
        'views/move.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
