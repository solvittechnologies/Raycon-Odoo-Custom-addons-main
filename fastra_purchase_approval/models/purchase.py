# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection_add=[('approve_level_1', 'Approve Level 1'),
                                            ('approve_level_2', 'Approve Level 2'),
                                            ('approve_level_3', 'Approve Level 3'),
                                            ('approve_level_4', 'Approve Level 4'),
                                            ('reject_level_1', 'Reject by Level 1'),
                                            ('reject_level_2', 'Reject by Level 2'),
                                            ('reject_level_3', 'Reject by Level 3'),
                                            ('reject_level_4', 'Reject by Level 4'),
                                            ])

    def action_button_approve_level(self):
        if self.env.user.has_group('fastra_purchase_approval.group_purchase_level_1'):
            self.write({'state': 'approve_level_1'})
        if self.env.user.has_group('fastra_purchase_approval.group_purchase_level_2'):
            self.write({'state': 'approve_level_2'})
        if self.env.user.has_group('fastra_purchase_approval.group_purchase_level_3'):
            self.write({'state': 'approve_level_3'})
        if self.env.user.has_group('fastra_purchase_approval.group_purchase_level_4'):
            self.write({'state': 'approve_level_4'})

    def action_button_reject_level(self):
        if self.env.user.has_group('fastra_purchase_approval.group_purchase_level_1'):
            self.write({'state': 'reject_level_1'})
        if self.env.user.has_group('fastra_purchase_approval.group_purchase_level_2'):
            self.write({'state': 'reject_level_2'})
        if self.env.user.has_group('fastra_purchase_approval.group_purchase_level_3'):
            self.write({'state': 'reject_level_3'})
        if self.env.user.has_group('fastra_purchase_approval.group_purchase_level_4'):
            self.write({'state': 'reject_level_4'})

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        if res:
            for order in self:
                if order.state == 'approve_level_4':
                    order._add_supplier_to_product()
                    # Deal with double validation process
                    if order.company_id.po_double_validation == 'one_step' or (order.company_id.po_double_validation == 'two_step' and order.amount_total < self.env.user.company_id.currency_id._convert(order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today())) or order.user_has_groups('purchase.group_purchase_manager'):
                        order.button_approve()
        return res