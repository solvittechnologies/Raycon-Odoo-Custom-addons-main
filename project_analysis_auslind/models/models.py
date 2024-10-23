# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class project_analysis_auslind(models.Model):
#     _name = 'project_analysis_auslind.project_analysis_auslind'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


class project_analysis(models.Model):
    _name = 'fastra.project.analysis'
    #_inherits = ['account']

    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('in_payment', 'In Payment'),  ('paid', 'Paid'), ('cancel', 'Cancelled'), ],
                             string='Status', index=True, readonly=True, default='draft',
                             track_visibility='onchange', copy=False,
                             help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
                             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
                             " * The 'In Payment' status is used when payments have been registered for the entirety of the invoice in a journal configured to post entries at bank reconciliation only, and some of them haven't been reconciled with a bank statement line yet.\n"
                             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
                             " * The 'Cancelled' status is used when user cancel invoice.")
    date_invoice = fields.Date(string='Date',
                               readonly=True, states={'draft': [('readonly', False)]}, index=True,
                               help="Keep empty to use the current date", copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer', change_default=True,
                                 readonly=True, states={'draft': [('readonly', False)]},
                                 track_visibility='always', ondelete='restrict', help="You can find a contact by its Name, TIN, Email or Internal Reference.")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, readonly=True, states={'draft': [('readonly', False)]},
                                  track_visibility='always')
    user_id = fields.Many2one('res.users', string='Created By', track_visibility='onchange',
                              readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user, copy=False)

    vat = fields.Monetary(string='V.A.T')

    pr = fields.Monetary(string='P.R')

    po_number = fields.Char('PO Number')

    project = fields.Selection([
        ('BIV','Biometric Identification and Verification'),
        ('DMW','Document Management and Workflow'),
        ('EL','E-Library'),
        ('HCM','Human Capital Management')], string = "Project Name")

    project_description = fields.Char('Description')

    project_duration = fields.Integer('Duration')

    project_location = fields.Char('Location')

    wht = fields.Monetary('W.H.T')

    invoice_line_ids = fields.One2many('project.analysis.line', 'job_line_ids', string='Project Lines',
                                       readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    amount = fields.Monetary('Total Amount Paid')

    amount_total = fields.Monetary(string='Implementation Cost',
                                compute='_compute_total_amount',
                                store=True,  # optional
                                )
    profit_loss = fields.Monetary(string='Profit / Loss',
                                compute='_compute_profit_loss',
                                store=True,  # optional
                                )

    @api.onchange("amount_total")
    @api.multi
    def _compute_profit_loss(self):
        amountDifference = 0
        for a in self:
            amountDifference = a.amount - a.amount_total
        self.profit_loss = amountDifference

    @api.depends('invoice_line_ids')
    @api.multi
    def _compute_total_amount(self):
        totalAmount = 0
        for a in self.invoice_line_ids:
            totalAmount += a.amount
        self.amount_total = totalAmount


class AccountInvoiceLine(models.Model):
    _name = "project.analysis.line"
    _description = "Project Line"

    job_id = fields.Many2one('product.product', string='Job',
                             ondelete='restrict', index=True)

    job_line_ids = fields.Many2one(
        'fastra.project.analysis', string='Job Reference', ondelete='cascade', index=True)

    amount = fields.Monetary(string='Amount', required=True)

    #price_total = fields.Monetary(string='Amount',readonly=True, help="Total amount for the job")

    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string='Project Account')

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, readonly=True, states={'draft': [('readonly', False)]},
                                  track_visibility='always')

    name = fields.Text(string='Description', required=True)

    account_id = fields.Many2one('account.account', string='Account', domain=[('deprecated', '=', False)],
                                 help="The expense account related to the selected job.")
