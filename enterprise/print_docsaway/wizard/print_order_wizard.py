# -*- coding: utf-8 -*-
from odoo import api, models


class PrintOrderWizard(models.TransientModel):

    _inherit = 'print.order.wizard'

    @api.onchange('provider_id')
    def _onchange_provider_id(self):
        if self.provider_id.provider == 'docsaway':
            self.currency_id = self.env['res.currency'].sudo().with_context(active_test=False).search([('name', '=', 'AUD')])
