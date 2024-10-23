# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.addons import decimal_precision as dp
from datetime import datetime, timedelta

# class fastra_gas(models.Model):
#     _name = 'fastra_gas.fastra_gas'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


class POSPump(models.Model):
    _name = 'pos.pump'


    name= fields.Char(string="Pump Name")
    point_of_sale = fields.Many2one('pos.config')
    current_meter_reading = fields.Float()
