# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models

# ----------------------------------------------------------
# Models
# ----------------------------------------------------------


class CrmPhonecall(models.Model):
    _name = "crm.phonecall"

    _order = "sequence, id"

    name = fields.Char('Call Summary', required=True)
    date = fields.Datetime('Date', default=lambda self: fields.Datetime.now())
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.uid)
    partner_id = fields.Many2one('res.partner', 'Contact')
    company_id = fields.Many2one('res.company', 'Company')
    description = fields.Text('Description')
    duration = fields.Float('Duration', help="Duration in minutes and seconds.")
    partner_phone = fields.Char('Phone')
    partner_mobile = fields.Char('Mobile')
    team_id = fields.Many2one('crm.team', 'Sales Team', index=True,
        default=lambda self: self.env['crm.team']._get_default_team_id(self.env.uid),
        help="Sales team to which Case belongs to.")
    in_queue = fields.Boolean('In Call Queue', default=True)
    sequence = fields.Integer('Sequence', index=True,
        help="Gives the sequence order when displaying a list of Phonecalls.")
    start_time = fields.Integer("Start time")
    state = fields.Selection([
        ('pending', 'Not Held'),
        ('cancel', 'Cancelled'),
        ('open', 'To Do'),
        ('done', 'Held'),
        ], string='Status', default='open', track_visibility='onchange',
        help='The status is set to To Do, when a case is created.\n'
             'When the call is over, the status is set to Held.\n'
             'If the call is not applicable anymore, the status can be set to Cancelled.')
    opportunity_id = fields.Many2one('crm.lead', 'Lead/Opportunity',
        ondelete='cascade', track_visibility='onchange')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_phone = self.partner_id.phone
            self.partner_mobile = self.partner_id.mobile

    @api.onchange('opportunity_id')
    def _onchange_opportunity(self):
        if self.opportunity_id:
            self.team_id = self.opportunity_id.team_id
            self.partner_id = self.opportunity_id.partner_id
            self.partner_phone = self.opportunity_id.phone\
                or self.partner_id.phone
            self.partner_mobile = self.opportunity_id.mobile\
                or self.partner_id.mobile

    @api.multi
    def schedule_another_phonecall(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'key2': 'client_action_multi',
            'src_model': "crm.phonecall",
            'res_model': "crm.schedule_phonecall",
            'multi': "True",
            'target': 'new',
            'context': {
                'phonecall_to_cancel': self.id,
                'default_name': self.name,
                'default_partner_id': self.partner_id.id,
                'default_user_id': self.user_id.id,
                'default_opportunity_id': self.opportunity_id.id,
                'default_partner_phone': self.partner_phone,
                'default_partner_mobile': self.partner_mobile,
                'default_team_id': self.team_id.id,
            },
            'views': [[False, 'form']],
        }

    @api.multi
    def action_button_to_opportunity(self):
        self.ensure_one()
        if not self.opportunity_id:
            self.opportunity_id = self.env['crm.lead'].create({
                'name': self.name,
                'partner_id': self.partner_id.id,
                'phone': self.partner_phone,
                'mobile': self.partner_mobile,
                'team_id': self.team_id.id,
                'description': self.description,
                'type': 'opportunity',
                'email_from': self.partner_id.email,
            })
        return self.opportunity_id.redirect_opportunity_view()

    @api.multi
    def init_call(self):
        self.start_time = int(time.time())

    @api.multi
    def hangup_call(self):
        stop_time = int(time.time())
        duration = float(stop_time - self.start_time)
        self.duration = float(duration/60.0)
        self.state = "done"
        return {"duration": self.duration}

    @api.multi
    def rejected_call(self):
        self.state = "pending"

    @api.multi
    def remove_from_queue(self):
        self.in_queue = False
        if(self.state == "open"):
            self.state = "cancel"
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
        }

    @api.one
    def get_info(self):
        return {"id": self.id,
                "description": self.description,
                "name": self.name,
                "state": self.state,
                "date": self.date,
                "duration": self.duration,
                "partner_id": self.partner_id.id,
                "partner_name": self.partner_id.name,
                "partner_image_small": self.partner_id.image_small,
                "partner_email": self.partner_id.email,
                "partner_title": self.partner_id.title.name,
                "partner_phone": self.partner_phone or self.partner_mobile or self.opportunity_id.phone or self.opportunity_id.partner_id.phone or self.opportunity_id.partner_id.mobile or False,
                "opportunity_name": self.opportunity_id.name,
                "opportunity_id": self.opportunity_id.id,
                "opportunity_priority": self.opportunity_id.priority,
                "opportunity_planned_revenue": self.opportunity_id.planned_revenue,
                "opportunity_title_action": self.opportunity_id.title_action,
                "opportunity_date_action": self.opportunity_id.date_action,
                "opportunity_company_currency": self.opportunity_id.company_currency.id,
                "opportunity_probability": self.opportunity_id.probability,
                "max_priority": self.opportunity_id._fields['priority'].selection[-1][0]}

    @api.model
    def get_list(self):
        return {"phonecalls": self.search([
            ('in_queue', '=', True),
            ('user_id', '=', self.env.user.id),
            ('date', '<=', fields.Datetime.now())],
            order='sequence,id')
            .get_info()}

    @api.model
    def get_new_phonecall(self, number):
        phonecall = self.create({
            'name': 'Call to ' + number,
            'partner_phone': number,
        })
        return {"phonecall": phonecall.get_info()}
