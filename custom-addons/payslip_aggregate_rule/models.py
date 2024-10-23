#-*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp

RULE_AMOUNT_TYPES_LST = [
        ('is_aggregate',    'Is an aggregate value (already a sum or subtration of other rules)'),
        ('to_sum',          'This term is summed'),
        ('to_sub',          'This term is subtracted'),
        ('other',           'Other role'),
        ]

class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'
    
    cat_amount_type = fields.Selection(
        RULE_AMOUNT_TYPES_LST, string="Type of amount", help="How this amount influences the salary NET total",
            required=True, default="to_sum")

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    rule_amount_type = fields.Selection(
        RULE_AMOUNT_TYPES_LST, string="Type of amount", help="How this amount influences the salary NET total",
                compute="_compute_rule_amount_type", store=True, readonly=True)
    @api.depends('category_id', 'category_id.cat_amount_type')
    def _compute_rule_amount_type(self):
        for rul in self:
            rul.rule_amount_type = rul.category_id.cat_amount_type
    
    is_aggregate = fields.Boolean(string='Is an aggregate value', compute="_compute_is_aggregate", store=True,
        help="Used to indicate if this rule is a sum of other rules.")
    @api.depends('rule_amount_type')
    def _compute_is_aggregate(self):
        for rul in self:
            rul.is_aggregate = (rul.rule_amount_type=='is_aggregate')

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'
    _description = 'Payslip Line'
    _order = 'contract_id, sequence'

    @api.model
    def create(self, values):
        if ('salary_rule_id' in values):
            if ('is_aggregate' not in values):
                values['is_aggregate'] = self.env['hr.salary.rule'].browse(values['salary_rule_id']).is_aggregate
            if ('rule_amount_type' not in values):
                values['rule_amount_type'] = self.env['hr.salary.rule'].browse(values['salary_rule_id']).rule_amount_type
        return super(HrPayslipLine, self).create(values)
