from odoo import fields, models, api


class EmployeeLoan(models.Model):
    _name = 'employee.loan'
    _description = 'Employee Loan'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    job_id = fields.Many2one('hr.job', 'Job Position', related="employee_id.job_id")
    allocation_date = fields.Datetime('Allocation Date', default=lambda self: fields.Datetime.now())
    employee_bank_account = fields.Char("Employee Bank Account")
    allocation_line_ids = fields.One2many('employee.loan.allocation.line', 'loan_id', string="Allocation Lines")
    loan_payment_ids = fields.One2many('employee.loan.payment.line', 'loan_id', string="Payment")


class EmployeeLoanAllocationLine(models.Model):
    _name = 'employee.loan.allocation.line'

    loan_id = fields.Many2one('employee.loan', "Loan")
    total_loan_amount = fields.Float('Total Loan Amount')
    loan_from_date = fields.Date('From Date')
    loan_to_date = fields.Date('To Date')
    loan_payment_method = fields.Selection([('month', 'Monthly'),
                                            ('year', 'Yearly')], string="Payment Method")
    loam_amount = fields.Float("Installment Amount")
    loan_narration = fields.Char('Loan Narration')


class EmployeeLoanPaymentLine(models.Model):
    _name = 'employee.loan.payment.line'

    loan_id = fields.Many2one('employee.loan', "Loan")
    total_amount = fields.Float('Total Amount')
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')