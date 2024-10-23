from odoo import fields, models, api,_
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import base64
from io import BytesIO




Months = [('January', 'January'),
          ('february', 'February'),
          ('march', 'March'),
          ('april', 'April'),
          ('may', 'May'),
          ('june', 'June'),
          ('july', 'July'),
          ('august', 'August'),
          ('september', 'September'),
          ('october', 'October'),
          ('november', 'November'),
          ('december', 'December')]


class SalariesExcelSheet(models.Model):
    _name = 'salaries.excel.sheet'
    _description = 'Salaries Excel Sheet'

    name = fields.Char("Payslip Name")
    location_id = fields.Many2one('stock.location', "Location")
    date_from = fields.Date(string='Date From',
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            )
    date_to = fields.Date(string='Date To',
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
                          )
    month = fields.Selection(Months, string="Month")
    employee_tag = fields.Char("Employee Tag")
    account_analytic_id = fields.Many2one('account.analytic.account', "Project")
    line_ids = fields.One2many('salaries.excel.line', 'salaries_excel_id', string="Lines")
    excel_file = fields.Binary('Excel File')
    file_name = fields.Char('File Name')

    def generate_excel(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)

        worksheet = workbook.add_worksheet('RENTAL VEHICLE Report')

        bold = workbook.add_format({'bold': True})
        border = workbook.add_format({'border': 1})
        format1 = workbook.add_format({'bold': True, 'border': 1})

        row = 0
        worksheet.write(row, 0, 'TRANSACTION REFERENCE NUMBER', format1)
        worksheet.write(row, 1, 'BENEFICIARY NAME', format1)
        worksheet.write(row, 2, 'PAYMENT AMOUNT', format1)
        worksheet.write(row, 3, 'PAYMENT DUE DATE', format1)
        worksheet.write(row, 4, 'BENEFICIARY CODE', format1)
        worksheet.write(row, 5, 'BENEFICIARY ACCOUNT NUMBER', format1)
        worksheet.write(row, 6, 'BENEFICIARY BANK SORT CODE', format1)
        worksheet.write(row, 7, 'DEBIT ACCOUNT NUMBER', format1)

        row += 1
        for line in self.line_ids:
            worksheet.write(row, 0, line.transaction_reference_number or '')
            worksheet.write(row, 1, line.beneficiary_name or '')
            worksheet.write(row, 2, line.payment_amount or '')
            worksheet.write(row, 3, line.payment_due_date and line.payment_due_date.strftime('%m/%d/%Y') or '')
            worksheet.write(row, 4, line.beneficiary_code or '')
            worksheet.write(row, 5, line.beneficiary_account_number or '')
            worksheet.write(row, 6, line.beneficiary_bank_sort_code or '')
            worksheet.write(row, 7, line.debit_account_number or '')
            row += 1

        workbook.close()
        file_data.seek(0)
        self.write(
            {'excel_file': base64.encodebytes(file_data.read()),
             'file_name': 'Salaries Excel Sheet.xlsx'})

        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=salaries.excel.sheet&id=" + str(self.id) + "&filename_field=filename&field=excel_file&download=true&filename=" + self.file_name,
            'target': 'current'
        }


class SalariesExcelSheetLine(models.Model):
    _name = 'salaries.excel.line'

    salaries_excel_id = fields.Many2one('salaries.excel.sheet', "Salaries Excel")
    transaction_reference_number = fields.Char('TRANSACTION REFERENCE NUMBER')
    beneficiary_name = fields.Char('BENEFICIARY NAME')
    payment_amount = fields.Float('PAYMENT AMOUNT')
    payment_due_date = fields.Date('PAYMENT DUE DATE')
    beneficiary_code = fields.Char('BENEFICIARY CODE')
    beneficiary_account_number = fields.Char('BENEFICIARY ACCOUNT NUMBER')
    beneficiary_bank_sort_code = fields.Char('BENEFICIARY BANK SORT CODE')
    debit_account_number = fields.Char('DEBIT ACCOUNT NUMBER')



