# -*- coding: utf-8 -*-

{
    'name': 'Fastra HR Customize',
    'version': '12.0.1.0.0',
    'summary': 'Fastra HR Customize',
    'depends': ['hr', 'stock', 'account', 'hr_menus', 'hr_timesheet', 'hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'data/payroll_sequence.xml',

        'views/hr_payslip_custom.xml',
        'views/salaries_excel_sheet.xml',
        'views/employee_loan.xml',
        'views/stock_location.xml',

        'reports/salaries_excel_sheet_report.xml',
        'reports/payroll_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
