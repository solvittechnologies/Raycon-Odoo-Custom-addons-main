# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HmrcSendWizard(models.TransientModel):
    _name = 'l10n_uk.hmrc.send.wizard'
    _description = "HMRC Send Wizard"

    @api.model
    def default_get(self, fields_list):
        res = super(HmrcSendWizard, self).default_get(fields_list)

        if not self.env.user.l10n_uk_user_token:
            res['need_login'] = True
            return res
        res['need_login'] = False
        # Check obligations: should be logged in by now
        self.env['l10n_uk.vat.obligation'].import_vat_obligations()

        obligations = self.env['l10n_uk.vat.obligation'].search([('status', '=', 'open')])
        if not obligations:
            raise UserError(_('You have no open obligations anymore'))
        return res

    need_login = fields.Boolean('Needs login')
    obligation_id = fields.Many2one('l10n_uk.vat.obligation', 'Obligation', domain=[('status', '=', 'open')])
    accept_legal = fields.Boolean('Accept Legal Statement')

    def send(self):
        if self.need_login:
            return self.env['hmrc.service']._login()
        # Check correct obligation and send it to the HMRC
        if not self.obligation_id:
            raise UserError(_('Please select an obligation first'))
        self.obligation_id.action_submit_vat_return()
        return True
