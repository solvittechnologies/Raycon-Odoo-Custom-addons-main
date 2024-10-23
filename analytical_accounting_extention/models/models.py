# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class analytical_accounting_extention(models.Model):
#     _name = 'analytical_accounting_extention.analytical_accounting_extention'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


# class QuotationAnalytical(models.Model):
#     _inherit = "sale.order"
#     analytical_account = fields.Many2one('account.analytic.account', string="Analytic Account")


class QuotationAnalyticalOder(models.Model):
    _inherit = "sale.order.line"
    analytical_account = fields.Many2one('account.analytic.account', string="Analytic Account")


# class PurchaseRequest(models.Model):
#     _inherit = ""
#     analytical_account = fields.Many2one('account.analytic.account', string="Analytic Account")
#
#
# class PurchaseOrder(models.Model):
#     _inherit = ""
#     analytical_account = fields.Many2one('account.analytic.account', string="Analytic Account")
#
#
# class SalesOrder(models.Model):
#     _inherit = ""
#     analytical_account = fields.Many2one('account.analytic.account', string="Analytic Account")
#
#
class InvoiceAnalytical(models.Model):
    _inherit = "account.invoice.line"
    analytical_account = fields.Many2one('account.analytic.account', string="Analytic Account")


class VendorBills(models.Model):
    _inherit = "account.move.line"
    analytical_account = fields.Many2one('account.analytic.account', string="Analytic Account")

#
# class Payment(models.Model):
#     _inherit = ""
#     analytical_account = fields.Many2one('account.analytic.account', string="Analytic Account")
#
#
# class JournalEntries(models.Model):
#     _inherit = ""
#     analytical_account = fields.Many2one('account.analytic.account', string="Analytic Account")
#
#
# class JournalItems(models.Model):
#     _inherit = ""
#     analytical_account = fields.Many2one('account.analytic.account', string="Analytic Account")
