# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    is_taxcloud = fields.Boolean(string='Use TaxCloud API')

    @api.multi
    def map_tax(self, taxes, product=None, partner=None):

        # Do not put taxes if the fiscal position is using taxcloud
        # It will be compute on the SO or Inv confirmation
        if self.is_taxcloud:
            return self.env['account.tax'].browse()
        else:
            return super(AccountFiscalPosition, self).map_tax(taxes, product=product, partner=partner)


class AccountFiscalPositionTax(models.Model):
    _inherit = 'account.fiscal.position.tax'

    # TO REMOVE IN MASTER
    tic_category_ids = fields.Many2many('product.tic.category', string="TIC Category")
    state_ids = fields.Many2many('res.country.state', string="Federal States")
    zip_codes = fields.Char("Zip")
