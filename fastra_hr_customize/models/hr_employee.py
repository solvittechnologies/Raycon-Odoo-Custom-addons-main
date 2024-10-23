from odoo import fields, models, api


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    total_loan_amount = fields.Float('Total Loan Amount')
    loan_from_date = fields.Date('From Date')
    loan_to_date = fields.Date('To Date')
    loan_payment_method = fields.Selection([('month', 'Monthly'),
                                            ('year', 'Yearly')], string="Payment Method")
    loam_amount = fields.Float("Installment Amount")
    loan_narration = fields.Char('Loan Narration')

