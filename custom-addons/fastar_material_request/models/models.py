# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError


class MaterialForm(models.Model):
    _name = "material.request"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('Approve', 'Approve'),
        ('cancel', 'Cancel'),
    ], string='Status', index=True, readonly=True, default='draft', copy=False,
    )
    name = fields.Many2one("res.users", String='Store Keeper', default=lambda self: self.env.user)
    # partner = fields.Char(String='Receive Name')
    partner = fields.Many2one("res.partner")
    source_location = fields.Many2one('stock.location')
    destination = fields.Char()
    date = fields.Date("Request Date", default=datetime.date(datetime.now()))
    date_release = fields.Date("Request Date")
    shipping_policy = fields.Selection([
        ('draft', 'Receive each product when available '),
        ('request', 'Receive all product at once'),
    ], default='draft')
    request_line = fields.One2many(comodel_name='material.request.line', inverse_name='material_request_id', string='Request Lines', store=True,)

    @api.multi
    def submit_request(self):
        for rec in self:
            for i in rec.request_line:
                product = self.env['product.product'].search([('id','=',i.product.id)])
                if i.qty_req > product.qty_available:
                    i.state = 'not_available'
                else:
                    i.state = 'available'
                    self.write({'state': 'request'})
                    # self.write({'date_realse': datetime.now() })

    @api.multi
    def approve(self):
        pass
        # for rec in self:
        #     for i in rec.request_line:
        #         product = self.env['product.product'].search([('id','=',i.product.id)])
        #         if i.qty_req < product.qty_available:
        #             product.write({'qty_available': qty_available - i.qty_req })
                    
        self.write({'state': 'Approve'})
        self.write({'date_realse': datetime.date(datetime.now()) })

    def cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    @api.onchange('request_line')
    def approve(self):
        pass
        # for rec in self:
        #     for i in rec.request_line:
        #         if i.qty_req > i.product.qty_available:
        #             i.state = 'not_available'
        #         else:
        #             i.state = 'available'



class MaterialFormLine(models.Model):
    _name = "material.request.line"

    name = fields.Char(default='/', readonly=1)
    route = fields.Many2one('account.journal')
    product = fields.Many2one('product.product')
    qty_req = fields.Integer(default=1)
    qty_req_inprogress = fields.Integer(default=1, readonly=1)
    qty_req_done = fields.Integer(default=1, readonly=1)
    material_request_id = fields.Many2one('material.request')
    # description = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')], string='Status', index=True, readonly=True, copy=False,default='draft')


class UserLocation(models.Model):
    _inherit = "stock.location"

    store_keeper = fields.Many2one('res.users', string="Store Keeper")
    project_manager = fields.Many2one('res.users', string="Project manager")

# class ReturnForm(models.Model):
#     _name = "return.invetory"

#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('request', 'Request'),
#         ('Approve', 'Approve'),
#     ], string='Status', index=True, readonly=True, default='draft',
#         track_visibility='onchange', copy=False,
#     )
#     partner = fields.Many2one("res.users", string='Release Name', default=lambda self: self.env.user)
#     # name = fields.Many2one('res.partner')
#     name = fields.Char()
#     source_location = fields.Many2one('stock.location')
#     destination = fields.Char()
#     date = fields.Date("Request Date", default=datetime.date(datetime.now()))
#     date_return = fields.Date("Request Date", readonly=True)
#     return_line = fields.One2many(comodel_name='return.invetory.line', inverse_name='qty_req', string='Request Lines', store=True,)


    # def cancel(self):
    #     self.write({'state': 'request'})

#     @api.multi
#     def approve(self):
#         for rec in self:
#             for i in rec.request_line:
#                 product = self.env['product.product'].search([('id','=',i.product.id)])
#                 if i.qty_req < i.product.qty_available:
#                     product.write({'qty_available': qty_available + i.qty_req })
                    
#         self.write({'state': 'Approve'})
#         self.write({'date_return': datetime.date(datetime.now()) })


# class ReturnFormLine(models.Model):
#     _name = "return.invetory.line"

#     product = fields.Many2one('product.product')
#     qty_req = fields.Integer()
#     description = fields.Text()
