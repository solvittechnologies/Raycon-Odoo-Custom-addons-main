# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _



class StockMoveLots(models.Model):
    _inherit = 'stock.move.lots'

    lot_barcode = fields.Char(related="lot_id.name")