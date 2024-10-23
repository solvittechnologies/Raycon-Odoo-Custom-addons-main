# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _name = 'account.invoice'

    analytical_ids_custom = fields.Char(string='Tags', compute='_get_account_analytical', store=True)

    @api.model
    @api.depends('invoice_line_ids')
    def _get_account_analytical(self):
        for rec in self:
            analytic_custom = ','.join([l.account_analytic_id.name if l.account_analytic_id else '' for l in rec.invoice_line_ids])
            rec.analytical_ids_custom = analytic_custom