{
    'name': 'hr_timesheet_sheet_timesheet_grid',
    'description': """
Hide hr_timesheet_sheet menu items.
    """,
    'depends': [
        'hr_timesheet_sheet', 'timesheet_grid',
    ],
    'data': [
        'data/hr_timesheet_sheet_timesheet_grid_data.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
