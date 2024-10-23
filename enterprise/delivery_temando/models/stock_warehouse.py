# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    temando_location = fields.Char(string="Temando Location", help="Set this field with your Temando Location reference to enable manifesting from this location.",
                                   oldname="x_temando_location")
