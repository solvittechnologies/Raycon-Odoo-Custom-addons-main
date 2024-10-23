# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError


class MaterialConsumtionForm(models.Model):
    _name = "material.consumtion"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting'),
        ('ready', 'Ready'),
        ('done', 'Done'),
    ], string='Status', index=True, readonly=True, default='draft', copy=False,
    )
    store_keeper = fields.Many2one("res.users", String='Store Keeper',  default=lambda self: self.env.user)
    project_manager = fields.Many2one("res.users", String='Project Manager')
    partner = fields.Char()
    source_location = fields.Many2one('stock.location')
    operation_type = fields.Many2one('stock.picking.type')
    date = fields.Date("Request Date", default=datetime.date(datetime.now()))
    request_date = fields.Date("Request Date")
    material_consumtion_line = fields.One2many(comodel_name='material.consumtion.line', inverse_name='material_consumtion_id', string='Request Lines', store=True,)
    shipping_policy = fields.Selection([
        ('draft', 'Receive each product when available '),
        ('request', 'Receive all product at once'),
    ], default='draft')
    procurement_group = fields.Char(readony=1)
    priority = fields.Selection([
        ('not_urgent', 'Not urgent'),
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('very_urgent', 'Very Urgent'),
    ])
    product_category = fields.Many2one('product.category')
    journal_id = fields.Many2one('account.move', readonly=1)

    @api.multi
    def submit_request(self):
        for rec in self:
            data1 =[]
            data2 = []
            for i in rec.material_consumtion_line:
                product = self.env['product.product'].search([('id','=',i.product.id)])
                if i.intial_demand < product.qty_available:
                    # product.write({'qty_available': qty_available - i.qty_req })
                    i.reserved = i.intial_demand
                    data1.append(i.reserved)
                else:
                    i.reserved = product.qty_available
                    # data2.append(i.)
            if len(data1) == len(rec.material_consumtion_line):
                self.write({'state': 'request'})
            else:
                self.write({'state': 'draft'})

    @api.multi
    def approve(self):
        
        pass

    @api.multi
    def check_button(self):
        for rec in self:
            for i in rec.material_consumtion_line:
                product = self.env['product.product'].search([('id','=',i.product.id)])
                if i.intial_demand < product.qty_available:
                    # product.write({'qty_available': qty_available - i.qty_req })
                    i.reserved = i.intial_demand
                else:
                    i.reserved = product.qty_available




class MaterialConsumtionFormLine(models.Model):
    _name = "material.consumtion.line"

    product = fields.Many2one('product.product', ondelete='cascade')
    intial_demand = fields.Integer(store=True)
    reserved = fields.Integer(default=0, readonly=1, store=True)
    material_consumtion_id = fields.Many2one('material.consumtion')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')], string='Done', index=True, readonly=True, copy=False,default='draft')

