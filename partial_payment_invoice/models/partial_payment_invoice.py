# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import AccessError, UserError

class PartialPaymentInvoice(models.Model):
    _name = 'partial.payment.invoice'
    
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], readonly=True, default='draft', string="Status")
    partner_id = fields.Many2one('res.partner', string='Partner')
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today)
    partial_payment_invoice_line_ids = fields.One2many('partial.payment.invoice.line', 'partial_payment_invoice_id', string = "Lines")
    journal_id = fields.Many2one('account.journal', string='Payment Journal', domain=[('type', 'in', ('bank', 'cash'))])
    
    def action_post(self):
        if self.partial_payment_invoice_line_ids:
            payment_method = self.env.ref('account.account_payment_method_manual_out')
            if payment_method:
                for line in self.partial_payment_invoice_line_ids:
                    val = {'journal_id':self.journal_id.id,
                       'payment_date':self.payment_date,
                       'payment_type':self.payment_type,
                       'partner_id':self.partner_id.id,
                       'partner_type':'supplier',
                       'payment_method_id': payment_method.id,
                       'amount':line.amount,
                       'invoice_ids':[(4, line.invoice_id.id)]
                    }
                    payment_id = self.env['account.payment'].create(val)
                    if payment_id:
                        payment_id.post()
            self.write({'state': 'posted'})
        else:
            raise UserError(_("Please Enter Some value in payment lines."))
            
    @api.onchange('payment_type')
    def _onchange_amount(self):
        self.journal_id=self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])], limit=1)
        
    
class PartialPaymentInvoiceLine(models.Model):
    _name = 'partial.payment.invoice.line'
    
    invoice_id = fields.Many2one('account.invoice',string="Invoices", copy=False)
    invoice_amount = fields.Monetary('Total Amount',related = 'invoice_id.amount_total_signed')
    residual_amount = fields.Monetary('Amount Due Total',related = 'invoice_id.residual_signed')
    currency_id = fields.Many2one('res.currency', string='Currency',related = 'invoice_id.currency_id')
    amount = fields.Float('Amount')
    partner_id = fields.Many2one('res.partner', string='Partner',related = 'partial_payment_invoice_id.partner_id')
    partial_payment_invoice_id = fields.Many2one('partial.payment.invoice',string = 'Partial Payment Invoice')
    
    
    
    