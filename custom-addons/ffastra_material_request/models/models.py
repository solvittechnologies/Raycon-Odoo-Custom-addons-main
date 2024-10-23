# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class ffastra_material_request(models.Model):
#     _name = 'ffastra_material_request.ffastra_material_request'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

class MaterialRequest(models.Model):
    _name = 'material.request'