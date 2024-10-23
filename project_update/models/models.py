# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError

class ProjectUpdate(models.Model):
    _inherit = 'fastra.project.analysis'
    custom_project_id = fields.One2many('project.custom', 'project_id')
    
    @api.multi
    @api.depends('purchase_total', 'petty_cash_line_custodian_total', 'petty_cash_line_total', 'account_voucher_total', 'custom_project_id')
    def get_actual_implementation_cost(self):
        for rec in self:
            gross_amount = 0.0
            for project_line in rec.custom_project_id:
                gross_amount += project_line.gross_salary
            rec.actual_implementation_cost = rec.purchase_total + rec.petty_cash_line_custodian_total + rec.petty_cash_line_total + rec.account_voucher_total + gross_amount 


class ProjectCustom(models.Model):
    _name = 'project.custom'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    net_salary = fields.Float(string='Net Salary')
    gross_salary = fields.Float(string='Gross Salary')
    basic_salary = fields.Float(string='Basic Salary')
    pay_amount = fields.Float(string='Pay Amount')
    ordinary_overtime = fields.Float(string='Ordinary Overtime')
    public_overtime = fields.Float(string='Public Overtime')
    sunday_overtime = fields.Float(string='Sunday Overtime')
    project_id = fields.Many2one('fastra.project.analysis')


class HRcustom(models.Model):
    _inherit = 'fastra.project.analysis'

    location = fields.Many2one('account.analytic.account')


    api.multi
    @api.onchange('project_detail_id')
    def _onchange_location_id(self):
        for rec in self:
            payroll_budg = rec.env['hr.payslip.custom'].search([('account_analytic_id', '=', rec.project_detail_id.id)])
            w = []
            for abc in payroll_budg.payslip_custom_line_ids:
                w.append((0, 0,{
                    'employee_id' : abc.employee_id,
                    'net_salary' : abc.net,
                    'gross_salary' : abc.gross,
                    'basic_salary' : abc.basic_salary,
                    'pay_amount' : abc.pay_amount,
                    'ordinary_overtime' : abc.ordinary_overtime,
                    'public_overtime' : abc.public_overtime,
                    'sunday_overtime' : abc.sunday_overtime,
                    # 'project_id' : abc.project_id,
                }))
            # for c in payroll_budg.payslip_custom_line_ids:
            #     w.append(
            #         (0, 0, {
            #             'employee_id': c.employee_id,
            #
            #         }), )
            self.custom_project_id = w
            print(w)

    #     # for rec in payroll_budg:


