# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError


class RequestForm(models.Model):
    _name = "request.invetory"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('Approve', 'Approve'),
    ], string='Status', index=True, readonly=True, default='draft', copy=False,
    )
    name = fields.Many2one("res.users", String='Storekeeper Name', default=lambda self: self.env.user)
    partner = fields.Char(String='Receiver Name')
    source_location = fields.Many2one('stock.location')
    destination = fields.Char(String='Destination Location')
    date = fields.Date("Request Date", default=datetime.date(datetime.now()))
    date_realse = fields.Date(String='Collected Date', readonly=True)
    date_returned = fields.Date("Returned Date")
    request_line = fields.One2many(comodel_name='request.invetory.line', string='Product Lines', inverse_name='qty_req', store=True,)

    @api.multi
    def submit_request(self):
        self.write({'state': 'request'})
        # for rec in self:
        #     for i in rec.request_line:
        #         product = self.env['product.product'].search([('id','=',i.product.id)])
        #         if i.qty_req > product.qty_available:
        #             i.state = 'not_available'
        #         else:
        #             i.state = 'available'
        #             self.write({'state': 'request'})
                    # self.write({'date_realse': datetime.now() })

    @api.multi
    def approve(self):
        # for rec in self:
        #     for i in rec.request_line:
        #         product = self.env['product.product'].search([('id','=',i.product.id)])
        #         if i.qty_req < product.qty_available:
        #             product.write({'qty_available': qty_available - i.qty_req })
                    
        self.write({'state': 'Approve'})
        self.write({'date_realse': datetime.date(datetime.now()) })

    

    # @api.multi
    # @api.onchange('request_line')
    # def approve(self):
    #     for rec in self:
    #         for i in rec.request_line:
    #             if i.qty_req > i.product.qty_available:
    #                 i.state = 'not_available'
    #             else:
    #                 i.state = 'available'



class RequestFormLine(models.Model):
    _name = "request.invetory.line"

    product = fields.Many2one('product.product')
    qty_req = fields.Integer(default=1)
    description = fields.Text()
    state = fields.Selection([
        ('available', 'Available'),
        ('not_available', 'Not Available'),
    ], string='Status', index=True, readonly=True, copy=False,)


class ReturnForm(models.Model):
    _name = "return.invetory"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('Approve', 'Approve'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
    )
    partner = fields.Many2one("res.users", string='Release Name', default=lambda self: self.env.user)
    # name = fields.Many2one('res.partner')
    name = fields.Char()
    source_location = fields.Many2one('stock.location')
    destination = fields.Char()
    date = fields.Date("Request Date", default=datetime.date(datetime.now()))
    date_return = fields.Date("Request Date", readonly=True)
    return_line = fields.One2many(comodel_name='return.invetory.line', inverse_name='qty_req', string='Request Lines', store=True,)


    def submit_request(self):
        self.write({'state': 'request'})

    @api.multi
    def approve(self):
        # for rec in self:
        #     for i in rec.request_line:
        #         product = self.env['product.product'].search([('id','=',i.product.id)])
        #         if i.qty_req < i.product.qty_available:
        #             product.write({'qty_available': qty_available + i.qty_req })
                    
        self.write({'state': 'Approve'})
        self.write({'date_return': datetime.date(datetime.now()) })


class ReturnFormLine(models.Model):
    _name = "return.invetory.line"

    product = fields.Many2one('product.product')
    qty_req = fields.Integer()
    description = fields.Text()
