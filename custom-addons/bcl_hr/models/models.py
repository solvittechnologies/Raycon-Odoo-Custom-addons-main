# -*- coding: utf-8 -*-

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Rule(models.Model):

    _inherit = "hr.salary.rule"

    contract_id = fields.Many2one('hr.contract', '')

class Contract(models.Model):

    _inherit = 'hr.contract'

    contract_salary_rule = fields.Many2many('hr.salary.rule',string='contract salary rule', related='struct_id.rule_ids')
    a_1 = fields.Float(string='Allowance 1')
    a_2 = fields.Float(string='Allowance 2')
    a_3 = fields.Float(string='Allowance 3')
    a_4 = fields.Float(string='Allowance 4')
    d_1 = fields.Float(string='Deduction 1')
    d_2 = fields.Float(string='Deduction 2')
    d_3 = fields.Float(string='Deduction 3')
    d_4 = fields.Float(string='Deduction 4')
    esa_active_flg = fields.Boolean(string='Loan Active', )
    esa_penalty_active = fields.Boolean(string='Penalty active', )
    esa_monthly_payment = fields.Float(
        string='Monthly Payment', )
    esa_penalty_amount = fields.Float(
        string='Penalty amount', )
    @api.multi
    @api.depends('struct_id')
    def onchange_field(self):
        for rule in self.struct_id.rule_ids:
            self.salary_rules = self.struct_id.rule_ids.ids

