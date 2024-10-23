# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    account_analytic_ids = fields.Many2many('account.analytic.account', string="Project", compute='get_project_from_line')

    @api.multi
    @api.depends('line_ids')
    def get_project_from_line(self):
        for rec in self:
            project_list = []
            for line in rec.line_ids:
                if line.analytic_account_id:
                    project_list.append(line.analytic_account_id.id)
            project_list = list(set(project_list))
            rec.account_analytic_ids = [(6, 0, project_list)]
