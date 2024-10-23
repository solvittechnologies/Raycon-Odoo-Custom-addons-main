# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    min_days_between_followup = fields.Integer(related='company_id.min_days_between_followup', string='Minimum days between two follow-ups *')

    @api.multi
    def open_followup_level_form(self):
        res_ids = self.env['account_followup.followup'].search([])

        return {
                 'type': 'ir.actions.act_window',
                 'name': 'Payment Follow-ups',
                 'res_model': 'account_followup.followup',
                 'res_id': res_ids and res_ids.ids[0] or False,
                 'view_mode': 'form,tree',
         }
