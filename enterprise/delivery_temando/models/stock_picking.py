# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    temando_carrier_name = fields.Char(string='Temando Carrier Name', copy=False)
    temando_delivery_method = fields.Char(string='Temando Delivery Method', copy=False)

    @api.multi
    def action_print_temando_manifest(self):
        self.ensure_one()

        if self.carrier_id.delivery_type == 'temando':
            return self.carrier_id.temando_get_manifest(self)[0]
        else:
            return False
