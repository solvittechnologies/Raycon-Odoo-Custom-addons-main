# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    temando_carrier_id = fields.Integer(string='Temando Carrier ID', copy=False)
    temando_carrier_name = fields.Char(string='Temando Carrier Name', copy=False)
    temando_delivery_method = fields.Char(string='Temando Delivery Method', copy=False)

    @api.multi
    def write(self, vals):
        carrier_id = vals.get('carrier_id')
        if carrier_id and self.env['delivery.carrier'].browse(carrier_id).delivery_type != 'temando':
            vals['temando_carrier_name'] = ''
            vals['temando_delivery_method'] = ''
        return super(SaleOrder, self).write(vals)
