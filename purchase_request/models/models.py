# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class purchase_request(models.Model):
#     _name = 'purchase_request.purchase_request'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


class PurchaseReqestForm(models.Model):
    _name = 'purchase_request_form.purchase_request_form'

    project_id = fields.Many2one('project.project', string="Project Id")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('qs_approve', 'QS Approve'),
        ('PM_approve', 'PM Approve'),
        ('Confirm', 'Finalized'),
        # ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
    )
    request_refrence = fields.Char('Request Refrence')
    requested_by = fields.Many2one('res.users')
    approved_by = fields.Many2one("res.users")
    request_date = fields.Date('Request Date')
    purchase_request = fields.One2many('purchase_request_form.purchase_request_line', 'element', string="Purchase Reguest")

    def submit_request(self):
        self.write({'state': 'request'})

    @api.multi
    def approve_qs(self):
        self.write({'state': 'qs_approve'})

    @api.multi
    def approve_pm(self):
        self.write({'state': 'PM_approve'})

    @api.multi
    def finalize(self):
        self.write({'state': 'Confirm'})


class PurchaseRequestLine(models.Model):
    _name = 'purchase_request_form.purchase_request_line'

    phases = fields.Char('phases')
    qty = fields.Integer('Qty')
    uom_project = fields.Float('UOM')
    # budget_item = fields.Char('Budget Items')
    analytical_account = fields.Many2one('account.analytic.account', string="Analytical Account")
    element = fields.Many2one('product.product')
    description = fields.Text('Description')
