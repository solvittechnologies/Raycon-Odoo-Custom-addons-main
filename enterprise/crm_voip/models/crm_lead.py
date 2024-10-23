# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.translate import _


class CrmLead(models.Model):
    _inherit = "crm.lead"
    in_call_center_queue = fields.Boolean("Is in the Call Queue", compute='_compute_has_call_in_queue')

    @api.one
    def _compute_has_call_in_queue(self):
        self.in_call_center_queue = bool(self.env['crm.phonecall'].search_count([
            ('opportunity_id', '=', self.id),
            ('in_queue', '=', True),
            ('state', '!=', 'done'),
            ('user_id', '=', self.env.user.id)
        ]))

    @api.multi
    def create_call_in_queue(self):
        for opp in self:
            self.env['crm.phonecall'].create({
                'name': opp.name,
                'duration': 0,
                'user_id': self.env.user.id,
                'opportunity_id': opp.id,
                'partner_id': opp.partner_id.id,
                'state': 'open',
                'partner_phone': opp.phone or opp.partner_id.phone,
                'partner_mobile': opp.partner_id.mobile,
                'in_queue': True,
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
        }

    # Function call by the stat button
    @api.multi
    def create_custom_call_in_queue(self):
        return {
            'type': 'ir.actions.act_window',
            'key2': 'client_action_multi',
            'src_model': "crm.phonecall",
            'res_model': "crm.schedule_phonecall",
            'multi': "True",
            'target': 'new',
            'context': {
                'default_name': self.name,
                'default_partner_id': self.partner_id.id,
                'default_user_id': self.env.uid,
                'default_opportunity_id': self.id,
                'default_partner_phone': self.phone or self.partner_id.phone,
                'default_partner_mobile': self.mobile or self.partner_id.mobile,
                'default_team_id': self.team_id.id,
            },
            'views': [[False, 'form']],
        }

    @api.multi
    def delete_call_in_queue(self):
        self.env['crm.phonecall'].search([
            ('opportunity_id', '=', self.id),
            ('in_queue', '=', True),
            ('user_id', '=', self.env.user.id)]).unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
        }

    @api.multi
    def log_new_phonecall(self):
        phonecall = self.env['crm.phonecall'].create({
            'name': self.name,
            'user_id': self.env.user.id,
            'opportunity_id': self.id,
            'partner_id': self.partner_id.id,
            'state': 'done',
            'partner_phone': self.phone or self.partner_id.phone,
            'partner_mobile': self.partner_id.mobile,
            'in_queue': False,
        })
        return {
            'name': _('Log a call'),
            'type': 'ir.actions.act_window',
            'key2': 'client_action_multi',
            'src_model': "crm.phonecall",
            'res_model': "crm.phonecall.log.wizard",
            'multi': "True",
            'target': 'new',
            'context': {'phonecall_id': phonecall.id,
                        'default_opportunity_id': phonecall.opportunity_id.id,
                        'default_name': phonecall.name,
                        'default_duration': phonecall.duration,
                        'default_description': phonecall.description,
                        'default_opportunity_name': phonecall.opportunity_id.name,
                        'default_opportunity_planned_revenue': phonecall.opportunity_id.planned_revenue,
                        'default_opportunity_title_action': phonecall.opportunity_id.title_action,
                        'default_opportunity_date_action': phonecall.opportunity_id.date_action,
                        'default_opportunity_probability': phonecall.opportunity_id.probability,
                        'default_partner_id': phonecall.partner_id.id,
                        'default_partner_name': phonecall.partner_id.name,
                        'default_partner_email': phonecall.partner_id.email,
                        'default_partner_phone': phonecall.opportunity_id.phone or phonecall.partner_id.phone,
                        'default_partner_image_small': phonecall.partner_id.image_small,},
                        'default_show_duration': self._context.get('default_show_duration'),
            'views': [[False, 'form']],
            'flags': {
                'headless': True,
            },
        }
