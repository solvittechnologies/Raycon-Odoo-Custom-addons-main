# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class fastra__pr__p_request(models.Model):
#     _name = 'fastra__pr__p_request.fastra__pr__p_request'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


class FastraExtention(models.Model):
    _inherit = "purchase.order"

    purchase_request_ = fields.Many2one('purchase.request', string="Purchase Request")
    location_id = fields.Many2one('stock.location', string="Location")
    description = fields.Text(string="Description")


    @api.onchange('purchase_request_')
    def porpulate_po(self):
        for rec in self:
            if rec.purchase_request_:
                for info in rec.purchase_request_:
                    # rec.date_order = str(info.date_start)
                    # rec.partner_id = info.requested_by.id
                    # rec.location = info.picking_type_id.id

                    appointment_line = [(5, 0, 0)]

                    for i in info.line_ids:
                        line = {
                            'product_id': i.product_id.id,
                            'name': i.name,
                            'date_planned': str(i.date_required),
                            'account_analytic_id': i.analytic_account_id,
                            'product_qty': i.product_qty,
                            'price_subtotal': i.estimated_cost,
                            'price_unit': i.estimated_cost / i.product_qty,
                            'analytic_tag_ids': i.analytic_tag_ids,
                            'product_uom': i.product_id.uom_id
                        }
                        appointment_line.append((0, 0, line))
                        rec.order_line = appointment_line


_STATES = [
    ('draft', 'Draft'),
    ('to_approve', 'To be approved'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('done', 'Done'),
    ('unfulfilled','unFulfilled'),
('fulfilled','Fulfilled')
]

class purchase_request_extend(models.Model):
    _inherit = "purchase.request"

    @api.model
    def _get_default_location(self):
        result = self.env['stock.location'].search([('store_keeper', '=', self.env.uid)])
        print(result,"result....location..")
        if len(result)==1:
            return result.id
        if len(result)>1:
            return result[0].id

    send_to = fields.Selection([(
		'procurement','Procurement'),('batching','Batching Plant')],default="procurement")
    location_id = fields.Many2one('stock.location', string="Location",default=_get_default_location)
    # state2 = fields.Selection([('unfulfilled','unFulfilled'),('fulfilled','Fulfilled')],default="unfulfilled")
    # state = fields.Selection(selection=_STATES,
    #                          string='Status',
    #                          index=True,
    #                          track_visibility='onchange',
    #                          required=True,
    #                          copy=False,
    #                          default='draft')\\\\\\\\\\\\\\\\\\\\\\\\\\\

class ProductTemplate(models.Model):
    _inherit = 'account.payment'

    journal_id = fields.Many2one("account.journal", domain="[()]")
