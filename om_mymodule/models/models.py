# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class om_mymodule(models.Model):
#     _name = 'om_mymodule.om_mymodule'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100