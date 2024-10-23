# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

class Kay_petty_cash(models.Model):
    _name="kay.petty.cash"

    name= fields.Char(string="Petty Cash name")
    custodian = fields.Many2one('res.partner',string="Custodian")
    custodian_account =  fields.Many2one('account.account',string="Custodian Account")
    amount = fields.Float(string="Amount Allocated",compute="_compute_amount_allocated",store=True)
    add_cash_line =fields.One2many("kay.petty.cash.add.line","petty_cash_id",string="Top up")
    amount_left = fields.Float(string="Amount left",compute="_compute_amount_left",store=True)
    journal_id= fields.Many2one("account.journal",string="Journal",default=lambda self: self.env['account.journal'].search([('name','=','Petty Cash')]))
    state = fields.Selection([
                  	('draft','Draft'),
       			 ('validate','Validated'),
				('closed','Closed')
        		 ],default='draft')
    cash_line = fields.One2many('petty.cash.line','petty_cash_id',string="Cash Lines")



    _sql_constraints = [
                     ('custodian_unique', 
                      'unique(custodian)',
                      'Please Choose another custodian - Custodian has to be unique!')
	]

    def action_cancel(self):
        for rec in self:
            for item in rec.add_cash_line:
                item.journal_entry.button_cancel()
                item.journal_entry.unlink()
                item.write({'state':'draft'})
            for line in rec.cash_line:
                line.write({'state':'draft'})
            rec.write({'state':'draft'})

    def action_validate(self):
        for rec in self:
            rec.write({'state':'validate'})

    @api.depends("add_cash_line")
    @api.multi
    def _compute_amount_allocated(self):
        self.ensure_one()
        amount_allocated = 0.0
        current_year = datetime.now().year
        previous_year = current_year - 1



        #amount used and amount allocated from previous year
        previous_amount_allocated = 0.0
        previous_amount_used = 0.0

        for b in self.cash_line:
            year = None
            if b.date:
                year = datetime.strptime(b.date, '%Y-%m-%d').year

            print(previous_year)
           
            if year == previous_year:
                previous_amount_used = previous_amount_used + b.amount  

        #get amount left using this year amount allocated,last year balnce and amount used this year
        for x in  self.add_cash_line:
            year = None
            if x.date:
                year = datetime.strptime(x.date, '%Y-%m-%d').year

            #get current year amount allocated
            if year == current_year:
                amount_allocated = amount_allocated + x.amount
            elif year == previous_year:
                previous_amount_allocated = previous_amount_allocated + x.amount
        previous_amount = previous_amount_allocated  - previous_amount_used
        self.amount = amount_allocated + previous_amount



    @api.depends("cash_line","amount")
    @api.multi
    def _compute_amount_left(self):
        self.ensure_one()
        amount_left = 0.0
        current_year = datetime.now().year
        for b in self.cash_line:
            year = None
            if b.date:
                year = datetime.strptime(b.date, '%Y-%m-%d').year
            if year == current_year:
                amount_left =amount_left + b.amount

        self.amount_left = self.amount - amount_left






class KayPettyCashAddCash(models.Model):
    _name= "kay.petty.cash.add.line"


    date = fields.Date(string="Payment Date")
    amount = fields.Float(string="Amount Allocated")
    journal_entry = fields.Many2one('account.move')
    petty_cash_id = fields.Many2one('kay.petty.cash', string='Petty Cash Reference',ondelete='cascade', index=True)
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env['res.currency'].search([('name','=','NGN')]))
    payable_account = fields.Many2one('account.account',string='Account payable')
    state = fields.Selection([
		('draft','Draft'),
               ('validate','Validated'),
                 ('cancel','Cancel')
                        ],default='draft')


    def action_cancel(self):
        for rec in self:
            rec.write({'state':'draft'})


    def action_validate(self):
        for rec in self:
            debit = credit = rec.currency_id.compute(rec.amount, rec.currency_id)
            move = {
             'name': '/',
             'journal_id': rec.petty_cash_id.journal_id.id,
             'date': rec.date,

             'line_ids': [(0, 0, {
                     'name': rec.petty_cash_id.name or '/',

                     'credit': credit,
                     'account_id': rec.payable_account.id,
                     'partner_id': rec.petty_cash_id.custodian.id,
                 }), (0, 0, {
                     'name': rec.petty_cash_id.name or '/',
                     'debit': debit,
                     'account_id': rec.petty_cash_id.custodian_account.id,
                     'partner_id': rec.petty_cash_id.custodian.id,
                 })]
            }
            move_id = self.env['account.move'].create(move)
            move_id.post()
            return rec.write({'state': 'validate','journal_entry':move_id.id})





class kay_petty_cash_line(models.Model):

     _name ="petty.cash.line"    

     description= fields.Text(string="Description")
     amount = fields.Float(string="Amount")
     journal_entry = fields.Many2one('account.move',string="Journal Entry")
     petty_line_account = fields.Many2one('account.account',string="Account")
     date = fields.Date(string="Expense Date")
     currency_id = fields.Many2one(
        'res.currency', string='Currency',default=lambda self: self.env['res.currency'].search([('name','=','NGN')]))
     petty_cash_id = fields.Many2one('kay.petty.cash', string='Petty Cash Reference',
        ondelete='cascade', index=True)
     state = fields.Selection([
                        ('draft','Not Posted'),
                         ('posted','Posted'),
                         ],default="draft")


     def action_cancel(self):
         self.journal_entry.button_cancel()
         self.journal_entry.unlink()
         return self.write({'state':'draft'})


     def action_post_line(self):
         for rec in self:
             debit = credit = rec.currency_id.compute(rec.amount, rec.currency_id)
             move = {
             'name': '/',
             'journal_id': rec.petty_cash_id.journal_id.id,
             'date': rec.date,

             'line_ids': [(0, 0, {
                     'name': rec.petty_cash_id.name or '/',
                     'credit': credit,
                     'account_id': rec.petty_cash_id.custodian_account.id,
                     'partner_id': rec.petty_cash_id.custodian.id,
                 }), (0, 0, {
                     'name': rec.petty_cash_id.name or '/',
                     'debit': debit,
                     'account_id': rec.petty_line_account.id,
                     'partner_id': rec.petty_cash_id.custodian.id,
                 })]
            }
             move_id = self.env['account.move'].create(move)
             move_id.post()
             return rec.write({'state': 'posted','journal_entry':move_id.id})


class Petty_cash_report(models.Model):
    _name = "petty.cash.report"

    user = fields.Many2one('res.partner',string="Petty Cash Custodian")
    year = fields.Selection([('2020','2020'),('2021','2021')],default="2021")
    lines = fields.One2many('petty.cash.report.line','petty_cash_report_ref',readonly=True)
    total_amount_allocated = fields.Float(string="Total Amount Allocated")
    previous_year_allocated_amount = fields.Float(string="Previous year amount")
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env['res.currency'].search([('name','=','NGN')]))  

    @api.multi
    @api.onchange('user','year')
    def compute_lines(self):
        if self.user and self.year:
            lines = []
            amount = 0.0
            previous_year_amount = 0.0
            previous_year_amount_allocated = 0.0
            previous_year_amount_used = 0.0
            previous_year = int(self.year) - 1

            cash_lines = self.env['kay.petty.cash.add.line'].search([('petty_cash_id.custodian.id','=',self.user.id)])
            used_cash_lines = self.env['petty.cash.line'].search([('petty_cash_id.custodian.id','=',self.user.id)])

            #filter data for curent year
            if cash_lines:
                for cash in cash_lines:
                    from datetime import datetime
                    year = None

                    if cash.date:
                        year = datetime.strptime(cash.date, '%Y-%m-%d').year

                    if str(year) == self.year:
                        amount = amount + cash.amount #compute total_amount_allocated
                        lines.append((0,0,{
			     'date':cash.date,
			     'journal_entry':cash.journal_entry.id,
			     'amount':cash.amount,
                             'state':cash.state

				}))
                    elif year == previous_year:
                        previous_year_amount_allocated = previous_year_amount_allocated + cash.amount

                for cash in used_cash_lines:
                    year = None
                    if cash.date:
                        year = datetime.strptime(cash.date, '%Y-%m-%d').year
                    if year == previous_year:
                        previous_year_amount_used = previous_year_amount_used + cash.amount

                rollover_amount = previous_year_amount_allocated  - previous_year_amount_used
                self.lines = lines
                self.total_amount_allocated = amount + rollover_amount
                self.previous_year_allocated_amount =  rollover_amount



class Petty_cash_report_lines(models.TransientModel):
    _name="petty.cash.report.line"

    petty_cash_report_ref = fields.Many2one('petty.cash.report')
    date = fields.Date()
    journal_entry = fields.Many2one('account.move') 
    state = fields.Char()
    amount = fields.Float(string="Amount Allocated") 
