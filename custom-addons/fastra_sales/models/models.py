# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class fastra_sales(models.Model):
#     _name = 'fastra_sales.fastra_sales'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


#Class SaleOrder(models.Model):
    #_inherit = 'sale.order'

    #vertical_manager_time_start = fields.Datetime(string="Vertical Manager Time Start", default=lambda self: fields.datetime.now(),readonly=True)
    #vertical_manager_time_end = fields.Datetime(string="Vertical Manager Time End",readonly=True)
    #vertical_manager_approve = fields.Boolean(string="Approved?",default=False)
    #vertical_manager_notification_send = fields.Boolean(String="Notified HR?",default=False)
    #sales_order_conversion_time_start = fields.Datetime(string="Sales order Conversion Tme Start",readonly=True)
    #sales_order_conversion_time_end = fields.Datetime(string="Sales Order Conversion Time End",readonly=True)
    #sales_order_conversion_done = fields.Datetime(string="Quotation Conversion")
    #sales_order_approval_time_start = fields.Datetime(string="Sales Order Approval Time Start",readonly=True)
    #sales_order_approval_time_end = fields.Datetime(string="Sales Order Apporval Time End",readonly=True)
    #sales_order_approval_done = fields.Boolean(string="Sales order Approved?",default=False)
    #freight_and_log = fields.Char(string="Freight and Logistics")
    #order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)],'so_to_approve': [('readonly', True)], 'done':[('readonly':True)]}, copy=True)
    #state = fields.Selection([
    #      ('draft', 'Quotation'),
    #      ('sent', 'Quote Sent'),
    #      ('to_accept', 'Quote Awaiting Acceptance'),
    #      ('quote_accepted', 'Quote Accepted'),
    #      ('quote_to_sales_order', 'Convert Quote To Sales Order'),
    #      ('sale', 'Sale Order Approved'),
    #      ('no_sale', 'On Hold'),
    #      ('done', 'Done'),
    #      ('cancel', 'Cancelled'),
    #      ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


    #def button_send_quote(self):
	#self.state = 'to_accept'


    #def to_accept(self):
	#self.state = 'qoute_accepted'  """



class CustomCRMActivities(models.Model):
    _name = "custom.crm.activities"

    lead_id =fields.Many2one('crm.lead',string='Crm Lead')
    client = fields.Many2one('res.partner',string='Customer/Client',store=True)
    stage = fields.Many2one('crm.stage',string='Current Stage',store=True)
    probability = fields.Integer(string='Probability',store=True)
    activity_type = fields.Many2one('mail.activity.type',string="Activity types")
    sales_person = fields.Many2one('res.users',string="Sales person",store=True)
    description = fields.Text()
    summary = fields.Text()
    feedback = fields.Text()
    complaints = fields.Text()
    schedule_upcoming_act = fields.Date(string="Schedule Upcoming Activity")
    status = fields.Selection([('draft','Draft'),('pending','Pending'),('postpone','Postponsed'),('done','Done')],default='draft')

    @api.onchange('lead_id')
    def onchange_lead(self):
        for rec in self:
            rec.client = rec.lead_id.partner_id.id
            rec.stage = rec.lead_id.stage_id.id
            rec.probability = rec.lead_id.probability
            rec.sales_person = rec.lead_id.user_id.id


    @api.multi
    def mark_done(self):
        for rec in self:
            rec.status = 'done'

    @api.multi
    def action_pending(self):
        for rec in self:
            rec.status = 'pending'

    @api.multi
    def action_postpone(self):
        for rec in self:
            rec.status = 'postpone'


class CRMExtend(models.Model):
    _inherit = "crm.lead"


    activities = fields.One2many('crm.activity.report','lead_id',string="Lead Activities")
    custom_activities = fields.One2many('custom.crm.activities','lead_id',string="Custom Lead Activities")





class SaleOrderExtended(models.Model):
    _inherit = "sale.order"

    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange', track_sequence=2,domain=lambda self: [("groups_id", "=", self.env.ref("sales_team.group_sale_salesman" ).id)], default=lambda self: self.env.user)
