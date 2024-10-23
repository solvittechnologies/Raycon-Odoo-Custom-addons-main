# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SalaryClass(models.Model):
    _name = "custom.hr.salary"


    @api.one
    @api.multi
    def _compute_currency(self):
        self.currency_id = self.env.user.company_id.currency_id.id
        return self.env.user.company_id.currency_id.id       


    name= fields.Char()
    start_date = fields.Date(string="Start date")
    payment_date = fields.Date(string="Payment date")
    end_date = fields.Date(string="End Date")
    manager = fields.Many2one('res.users',string="Payment Manager")
    salary_line = fields.One2many('station.salary.line','station_salary_id',string="Salary Line")
    total_amount = fields.Float(string="Total Amount",store=True,readonly=True)
    move_id = fields.Many2one('account.move',string="Journal Entry")
    journal_id = fields.Many2one('account.journal',string="Salary Payment Journal")
    currency_id = fields.Many2one('res.currency', string='Currency',default=_compute_currency,store=True)
    state = fields.Selection([
                        ('draft','Draft'),
                        ('awaiting','Awaiting Approval'),
                        ('approved','Approved'),
                         ('validated','Validated')
                         ],default='draft')

    @api.multi
    def action_send(self):
        for rec in self:
            rec.state = 'awaiting'

   
    @api.multi
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
   
    @api.multi
    def action_cancel(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def action_reject(self):
        for rec in self:
            rec.state = 'draft'
 


    @api.multi
    def action_post_payment_entry(self):
        for rec in self:
            debit = credit = rec.currency_id.compute(rec.total_amount, rec.currency_id)           
            #if rec.state == 'draft':
            #     raise UserError(_("Only a Submitted payment can be posted. Trying to post a payment in state %s.") % rec.state)
 
            #sequence_code = 'hr.advance.sequence'
            #rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.end_date).next_by_code(sequence_code)

            move = {
                 'name': '/',
                 'journal_id': rec.journal_id.id,
                 'date': rec.end_date,
 
                 'line_ids': [(0, 0, {
                       'name': rec.name or '/',
                       'debit': debit,
                       'account_id':rec.journal_id.default_debit_account_id.id,

                     }), (0, 0, {
                        'name': rec.name or '/',
                        'credit': credit,
                        'account_id': rec.journal_id.default_credit_account_id.id,

                     })]
             }
            move_id = self.env['account.move'].create(move)
            move_id.post()    
            return rec.write({'state': 'validated', 'move_id': move_id.id})

    @api.multi
    @api.onchange("salary_line","journal_id")
    def _compute_amount_total(self):
        for rec in self:
            amount_total = 0
            for line in rec.salary_line:
                amount_total = line.amount + amount_total
            rec.total_amount = amount_total



class salary_line_class(models.Model):
    _name = "station.salary.line"

    employee = fields.Many2one('res.users',string="Employee")
    amount = fields.Float(string="Amount",store=True)
    description= fields.Text(string="Description")
    station_salary_id = fields.Many2one('custom.hr.salary',string="HR Salary",ondelete="cascade", index=True)
    gross_amount = fields.Float(string="Gross Pay")
    deductions = fields.Float(string="Deduction")
    bonus = fields.Float(string="Bonus")


    @api.multi
    @api.onchange("gross_amount","deductions","bonus")
    def __onchange_amount(self):
        amount_total = 0
        for rec in self:
           amount_total = rec.gross_amount + rec.bonus - rec.deductions
           rec.amount = amount_total
           self.update({'amount':amount_total})
