# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class fastra_location_user(models.Model):
#     _name = 'fastra_location_user.fastra_location_user'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

class AddUserLocation(models.Model):
    _inherit = 'res.users'

    location_id = fields.Many2one('stock.location')