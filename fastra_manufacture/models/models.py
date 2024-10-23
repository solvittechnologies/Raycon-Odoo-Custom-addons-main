# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class fastra_manufacture(models.Model):
#     _name = 'fastra_manufacture.fastra_manufacture'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


class ManufacturerExtention(models.Model):
    _inherit = 'mrp.production'

    labour = fields.One2many('mrp.labour', 'product', string="Labour")
    material = fields.One2many('mrp.material', 'product', string="Material")


class ManufacturerLabour(models.Model):
    _name = 'mrp.labour'
    _description = 'Labour'

    product = fields.Many2one(string="Product")
    qty = fields.Integer(string="Quantity")
    rate = fields.Float(string="Rate")
    total = fields.Float(string="Total")


class ManufacturerMaterial(models.Model):
    _name = 'mrp.material'
    _description = 'Labour'

    product = fields.Many2one(string="Product")
    qty = fields.Integer(string="Quantity")
    rate = fields.Float(string="Rate")
    total = fields.Float(string="Total")
