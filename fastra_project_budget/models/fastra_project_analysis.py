# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountWHT(models.Model):
    _name = 'account.wht'

    name = fields.Float(string="Amount", digits=(16, 4))

class ModelName(models.Model):
    _name = 'project.budget.taxes'
    _description = 'Project Budget Taxes'

    tax_id = fields.Many2one('account.tax', string="Tax")
    tax_amount = fields.Float("Amount")
    budget_id = fields.Many2one('fastra.project.analysis', string="Budget")

class ProjectAnalysis(models.Model):
    _name = 'fastra.project.analysis'
    _inherit = ['fastra.project.analysis', 'mail.thread']

    state = fields.Selection(selection_add=[
                                            ('draft', 'Draft'),
                                            ('send_for_approval', 'Send for Approval'),
                                            ('approved', 'Approved'),
                                            ('reject', 'Rejected'),
                                            ], default='draft')
    # project_detail_id = fields.Many2one('project.details', string="Project")
    project_manager = fields.Many2one('res.users',"Project Manager")
    project_description = fields.Char("Project Description")
    project_duration = fields.Char("Project Duraion")
    request_date = fields.Date("Request Date")
    project_account_code = fields.Char("Project Account Code")
    project_location = fields.Many2one('stock.location',"Project Location")
    site = fields.Char("Site ID")
    invoice_line_ids = fields.One2many('project.analysis.line', 'job_line_ids', string='Project Lines',
                                       readonly=True, states={'draft': [('readonly', False)], 'approved': [('readonly', False)]}, copy=True)
    account_id = fields.Many2one('account.account', 'Account',  domain="[('deprecated', '=', False)]")
    voucher_ids = fields.Many2many('account.voucher', string="Receipts")
    project_detail_id = fields.Many2one('account.analytic.account', string="Project")
    purchase_order_line_ids = fields.Many2many('account.invoice', string="Invoices", compute='compute_project_detail_id')
    petty_cash_line_custodian_ids = fields.Many2many('kay.petty.cash.add.line', string="Petty Cash Custodian Lines",  compute='compute_project_detail_id')
    petty_cash_line_ids = fields.Many2many('purchase.request.kay.petty.cash', string="Petty Cash Lines",  compute='compute_project_detail_id')
    purchase_total = fields.Float(string="Total", compute='compute_total_amount')
    petty_cash_line_custodian_total = fields.Float(string="Total", compute='compute_total_amount')
    petty_cash_line_total = fields.Float(string="Total", compute='compute_total_amount')
    actual_implementation_cost = fields.Monetary('Actual Implementation Cost', compute="get_actual_implementation_cost")
    net_contract_value = fields.Monetary('Gross Contract Value', compute="get_net_contract_value")
    bill_amount = fields.Float('Bill 1')
    profit_loss = fields.Monetary(string='Profit / Loss',
                                compute='_compute_profit_loss_amount',
                                store=False,  # optional
                                )
    account_voucher_ids = fields.Many2many('account.voucher', string="Other Payment",  compute='compute_project_detail_id')
    account_voucher_total = fields.Float(string="Total", compute='compute_voucher_total_amount')
    tax_id = fields.Many2many('account.tax', string="Tax")
    tax_amount = fields.Float("Tax Amount", compute='get_net_contract_value')
    tax_breakout_ids = fields.One2many('project.budget.taxes', 'budget_id', string='Tax Amount', compute='get_tax_brakout')
    # wht_id = fields.Many2one('account.wht', string="WHT")
    # wht_amount = fields.Float("WHT Amount", compute='get_net_contract_value')
    wht_amount = fields.Float("WHT")
    contingency_amount = fields.Float("Contingency")

    @api.multi
    @api.depends('tax_id')
    def get_tax_brakout(self):
        for rec in self:
            rec.tax_breakout_ids = [(6, 0, [])]
            vals = []
            for tax in rec.tax_id:
                vals.append((0, 0, {'tax_id': tax.id, 'tax_amount': (rec.amount * tax.amount) / 100}))
            if vals:
                rec.tax_breakout_ids = vals

    @api.multi
    def compute_voucher_total_amount(self):
        for rec in self:
            line_total = 0.0
            for line in rec.account_voucher_ids:
                line_total += line.amount
            rec.account_voucher_total += line_total
    
    @api.multi
    @api.depends('purchase_total', 'petty_cash_line_custodian_total', 'petty_cash_line_total', 'account_voucher_total')
    def get_actual_implementation_cost(self):
        for rec in self:
            rec.actual_implementation_cost = rec.purchase_total + rec.petty_cash_line_custodian_total + rec.petty_cash_line_total + rec.account_voucher_total 
    
    @api.multi
    @api.depends('amount', 'bill_amount', 'tax_id', 'contingency_amount')
    def get_net_contract_value(self):
        for rec in self:
            # wht_amount = rec.wht_id.name if rec.wht_id else 0.0
            # wht = (rec.amount * wht_amount) / 100
            # rec.wht_amount = wht
            # rec.net_contract_value = rec.amount - (tax + wht + rec.bill_amount)
            tax_amount = 0.0
            for tax in rec.tax_id:
                tax_amount += (rec.amount * tax.amount) / 100
            rec.tax_amount = tax_amount
            rec.net_contract_value = rec.amount + tax_amount + rec.contingency_amount
            
            
    @api.multi
    @api.depends('net_contract_value','actual_implementation_cost', 'wht_amount', 'bill_amount', 'amount')
    def _compute_profit_loss_amount(self):
        for rec in self:
            rec.profit_loss = rec.amount - rec.actual_implementation_cost - rec.wht_amount - rec.bill_amount 
    
    @api.multi
    @api.depends('purchase_order_line_ids', 'petty_cash_line_custodian_ids', 'petty_cash_line_ids')
    def compute_total_amount(self):
        for rec in self:
            po_total = 0.0
            petty_cash_costodial_total = 0.0
            petty_cash_total = 0.0
            for po_line in rec.purchase_order_line_ids:
                po_total += po_line.amount_total
            for custodial_line in rec.petty_cash_line_custodian_ids:
                petty_cash_costodial_total += custodial_line.amount
            for petty_line in rec.petty_cash_line_ids:
                petty_cash_total += petty_line.amount
            rec.purchase_total = po_total
            rec.petty_cash_line_custodian_total = petty_cash_costodial_total
            rec.petty_cash_line_total = petty_cash_total 
    
    def action_button_send_for_approval(self):
        self.write({'state': 'send_for_approval'})

    def action_button_project_budget_approve(self):
        self.write({'state': 'approved'})

    def action_button_project_budget_reject(self):
        self.write({'state': 'reject'})
        
    def create_receipt(self):
        vals = {'account_id': self.account_id.id,
                'voucher_type': 'sale',
                }
        voucher_id = self.env['account.voucher'].create(vals)
        self.voucher_ids = [(4, voucher_id.id)]
    
    def action_view_receipts(self):
        if not self.voucher_ids:
            raise UserError(_("There is no Receipt for this Project Budget"))
        action = self.env.ref('account_voucher.action_sale_receipt').read()[0]
        action['domain'] = [('id', 'in', self.voucher_ids.ids)]
        return action

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.account_id = self.partner_id.property_account_receivable_id or self.partner_id.property_account_payable_id
            
    @api.multi
    @api.depends('project_detail_id')
    def compute_project_detail_id(self):
        for record in self:
            record.purchase_order_line_ids = [(6, 0, [])]
            record.petty_cash_line_custodian_ids = [(6, 0, [])]
            record.petty_cash_line_ids = [(6, 0, [])]
            record.account_voucher_ids = [(6, 0, [])]
            if record.project_detail_id:
                invoice_list = []
                account_invoice_line_ids = self.env['account.invoice.line'].search([('account_analytic_id','=',record.project_detail_id.id),
                                                                                   ('invoice_id.state','in',['paid'])])
                for line in account_invoice_line_ids:
                    invoice_list.append(line.invoice_id.id)
                invoice_list = list(set(invoice_list))
                record.purchase_order_line_ids = [(6, 0, invoice_list)]
            
                petty_cash_custodian_line_list = []
                petty_cash_line_list = []
                for petty_cash_id in self.env['kay.petty.cash'].search([('name','=',record.project_detail_id.id)]):
                    for line in petty_cash_id.add_cash_line:
                        if line.state == 'validate':
                            petty_cash_custodian_line_list.append(line.id)
                    for cash_line_id in petty_cash_id.purchase_request_petty_cash_lines:
                        if petty_cash_id.state == 'approved':
                            petty_cash_line_list.append(cash_line_id.id)
                    # for cash_line_id in petty_cash_id.cash_line:
                    #     if cash_line_id.state == 'posted':
                    #         petty_cash_line_list.append(cash_line_id.id)

                record.petty_cash_line_custodian_ids = [(6, 0, petty_cash_custodian_line_list)]
                record.petty_cash_line_ids = [(6, 0, petty_cash_line_list)]
                
                account_voucher_list = []
                for account_voucher_line_id in self.env['account.voucher.line'].search([('account_analytic_id','=',record.project_detail_id.id),
                                                                              ('voucher_id.journal_id.type','=','purchase'),
                                                                              ('voucher_id.voucher_type','=','purchase')]):
                    account_voucher_list.append(account_voucher_line_id.voucher_id.id)
                record.account_voucher_ids = [(6, 0, account_voucher_list)]
            


class ProjectAnalysisLine(models.Model):
    _inherit = "project.analysis.line"

    state = fields.Selection(related='job_line_ids.state', store=True)

    @api.onchange('job_line_ids', 'job_line_ids.currency_id')
    def onchange_project_budget_currency(self):
        self.currency_id = self.job_line_ids.currency_id