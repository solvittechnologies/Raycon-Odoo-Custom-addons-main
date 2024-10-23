# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

_STATES = [
    ('draft', 'Draft'),
    ('to_approve', 'To be approved'),
    ('approved', 'Approved'),
    ('validate','Validated'),
    ('posted', 'Posted'),
    ('done', 'Done'),
    ('rejected', 'Rejected'),
    ('closed','Closed'),
]

class Kay_petty_cash(models.Model):
    _inherit = "kay.petty.cash"
    
    state = fields.Selection(selection=_STATES,default='draft')
    custodian = fields.Many2one('res.users',string="Custodian")
    custodian_id = fields.Many2one('hr.employee','Custodian')
    partner_id = fields.Many2one('res.partner', string="Partner")
    location = fields.Many2one('stock.location','Location')
    purchase_request_petty_cash_lines = fields.One2many('purchase.request.kay.petty.cash', 'key_petty_cash_id', string="Lines")
    cancel_reason = fields.Char(
        string="Reason for Rejection",
        readonly=True)
    account_tax_id = fields.Many2one('account.tax', 'Tax')
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    move_ids = fields.Many2many('account.move', 'kay_petty_cash_move_rel', 'kay_petty_cash_id', 'move_id',
                                string="Moves")
    invoice_count = fields.Integer(compute='_invoice_count', string='# Invoice', copy=False)
    
    @api.multi
    def button_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def button_to_approve(self):
        return self.write({'state': 'to_approve'})

    @api.multi
    def button_approved(self):
        return self.write({'state': 'approved'})

    @api.multi
    def button_rejected(self):
        return self.write({'state': 'rejected'})

    @api.multi
    def button_post(self):
        move_list = []
        for line in self.purchase_request_petty_cash_lines:
            if not line.journal_id:
                raise UserError(_('Journal is not set in Lines!! Please Set Journal.'))
            if not line.account_credit or not line.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': line.name if line.name else line.key_petty_cash_id.name.name,
                'debit': line.amount,
                'credit': 0.0,
                'account_id': line.account_debit.id,
            }
            credit_vals = {
                'name': line.name if line.name else line.key_petty_cash_id.name.name,
                'debit': 0.0,
                'credit': line.amount,
                'account_id': line.account_credit.id,
            }
            vals = {
                'journal_id': line.journal_id.id,
                'date': datetime.now().date(),
                'ref': line.name if line.name else line.key_petty_cash_id.name.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            move_list.append(move.id)
        return self.write({'state': 'posted', 'move_ids': [(4, move) for move in move_list]})

    @api.multi
    def _invoice_count(self):
        self.invoice_count = len(self.move_ids.ids)

    @api.multi
    def button_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.move_ids.ids)],
        }

    
class PurchaseRequestKayPettyCash(models.Model):
    _name = "purchase.request.kay.petty.cash"
    
    key_petty_cash_id = fields.Many2one('kay.petty.cash', string="Petty Cash")
    name = fields.Char('Request Description')
    date = fields.Date('Request Date')
    amount = fields.Float('Request Amount')
    account_tax_id = fields.Many2one('account.tax', 'Tax')
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    amount_total_words = fields.Char("Total (In Words)", compute="_compute_amount_total_words")
    bank_id = fields.Many2one('res.bank',related='partner_bank_id.bank_id',string='bank')

    @api.depends('amount_total')
    def _compute_amount_total_words(self):
        for invoice in self:
            invoice.amount_total_words = invoice.currency_id.amount_to_text(invoice.amount_total)

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            if not line.account_id or line.display_type:
                continue
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.discount_rate > 0 or line.discount_fixed > 0:
                taxes = line.invoice_line_tax_ids.compute_all(line.price_subtotal, self.currency_id, 1, line.product_id,
                                                              self.partner_id)['taxes']
            else:
                taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id,
                                                      self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    discount_type = fields.Selection([('percentage', 'Percentage'), ('amount', 'Amount')], string='Discount Type', default='amount')
    discount_rate = fields.Float(string='Discount Rate', digits=dp.get_precision('Product Price'), default=0.0)
    discount_fixed = fields.Monetary(string='Discount', digits=dp.get_precision('Product Price'), default=0.0, track_visibility='always')
    delivery_cost = fields.Monetary('Delivery')


    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date', 'discount_type', 'discount_fixed', 'discount_rate',
                 'delivery_cost')
    def _compute_price(self):
        for rec in self:
            currency = rec.invoice_id and rec.invoice_id.currency_id or None
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            taxes = False
            if rec.invoice_line_tax_ids:
                taxes = rec.invoice_line_tax_ids.compute_all(price, currency, rec.quantity, product=rec.product_id,
                                                              partner=rec.invoice_id.partner_id)

            subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else rec.quantity * price
            discount = 0.0
            if rec.discount_type == 'amount':
                discount = rec.discount_fixed
            if rec.discount_type == 'percentage':
                discount = (rec.price_unit * rec.quantity * rec.discount_rate) / 100
            rec.price_subtotal = subtotal - discount + rec.delivery_cost
            rec.price_total = taxes['total_included'] if taxes else rec.price_subtotal
            if rec.invoice_id.currency_id and rec.invoice_id.currency_id != rec.invoice_id.company_id.currency_id:
                currency = rec.invoice_id.currency_id
                date = rec.invoice_id._get_currency_rate_date()
                price_subtotal_signed = currency._convert(price_subtotal_signed, rec.invoice_id.company_id.currency_id,
                                                          rec.company_id or rec.env.user.company_id,
                                                          date or fields.Date.today())
            sign = rec.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
            rec.price_subtotal_signed = price_subtotal_signed * sign
