# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools.translate import _


class CrmPhonecallLogWizard(models.TransientModel):
    _name = 'crm.phonecall.log.wizard'

    description = fields.Text('Description')
    name = fields.Char('Call Summary', readonly=True)
    opportunity_id = fields.Integer('Lead/Opportunity', readonly=True)
    opportunity_name = fields.Char('Lead/Opportunity name', readonly=True)
    opportunity_planned_revenue = fields.Char('Planned Revenue', readonly=True)
    opportunity_probability = fields.Float('Probability', readonly=True)
    partner_id = fields.Integer('Partner id', readonly=True)
    partner_name = fields.Char('Partner', readonly=True)
    partner_email = fields.Char('Email', readonly=True)
    partner_phone = fields.Char('Phone', readonly=True)
    partner_image_small = fields.Char('Partner image', readonly=True)
    duration = fields.Char('Duration', readonly=True)
    reschedule_option = fields.Selection([
        ('no_reschedule', "Don't Reschedule"),
        ('1d', 'Tomorrow'),
        ('7d', 'In 1 Week'),
        ('15d', 'In 15 Day'),
        ('2m', 'In 2 Months'),
        ('custom', 'Specific Date')
    ], 'Schedule A New Call', required=True, default="no_reschedule")
    reschedule_date = fields.Datetime(
        string='Specific Date',
        default=lambda *a: datetime.now() + timedelta(hours=2))
    next_activity_id = fields.Many2one("crm.activity", "Next Activity")
    new_title_action = fields.Char('Next Action')
    new_date_action = fields.Date('Next Action Date')
    show_duration = fields.Boolean('Show Duration')
    custom_duration = fields.Float('Custom Duration', default=0)
    in_automatic_mode = fields.Boolean('In Automatic Mode')

    def schedule_again(self):
        new_phonecall = self.env['crm.phonecall'].create({
            'name': self.name,
            'duration': 0,
            'user_id': self.env.user.id,
            'opportunity_id': self.opportunity_id,
            'partner_id': self.partner_id,
            'state': 'open',
            'partner_phone': self.partner_phone,
            'in_queue': True,
        })
        if self.reschedule_option == "7d":
            new_phonecall.date = datetime.now() + timedelta(weeks=1)
        elif self.reschedule_option == "1d":
            new_phonecall.date = datetime.now() + timedelta(days=1)
        elif self.reschedule_option == "15d":
            new_phonecall.date = datetime.now() + timedelta(days=15)
        elif self.reschedule_option == "2m":
            new_phonecall.date = datetime.now() + timedelta(weeks=8)
        elif self.reschedule_option == "custom":
            new_phonecall.date = self.reschedule_date

    @api.multi
    def modify_phonecall(self, phonecall):
        values = {}
        values.update(description=self.description)
        if(self.opportunity_id):
            opportunity = self.env['crm.lead'].browse(self.opportunity_id)
            if self.next_activity_id:
                opportunity.write({
                    'next_activity_id': self.next_activity_id.id,
                    'title_action': self.new_title_action,
                    'date_action': self.new_date_action,
                })
            if (self.show_duration):
                mins = int(self.custom_duration)
                sec = (self.custom_duration - mins)*0.6
                sec = '%.2f' % sec
                time = str(mins) + ":" + sec[-2:]
                message = _("Call %s min(s)") % time
                values.update(duration=self.custom_duration)
            else:
                message = _("Call %s min(s)") % self.duration
            if(self.description):
                message += _(" about %s") % self.description
            opportunity.message_post(message)
        phonecall.write(values)
        if self.reschedule_option != "no_reschedule":
            self.schedule_again()

    @api.multi
    def save(self):
        phonecall = self.env['crm.phonecall'].browse(self._context.get('phonecall_id'))
        self.modify_phonecall(phonecall)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
            'params': {'in_automatic_mode': self.in_automatic_mode},
        }

    @api.multi
    def save_go_opportunity(self):
        phonecall = self.env['crm.phonecall'].browse(self._context.get('phonecall_id'))
        self.modify_phonecall(phonecall)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
            'params': {'go_to_opp': True,
                       'opportunity_id': self.opportunity_id,
                       'in_automatic_mode': self.in_automatic_mode},
        }
