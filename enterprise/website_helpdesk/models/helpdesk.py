# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from odoo.addons.website.models.website import slug
from odoo import api, exceptions, fields, models


class HelpdeskTicket(models.Model):
    _inherit = ['helpdesk.ticket']

    access_token = fields.Char(
        'Security Token', copy=False, default=lambda self: str(uuid.uuid4()),
        required=True)

    @api.multi
    def get_access_action(self):
        """ Instead of the classic form view, redirect to website for portal users
        that can read the ticket if the team is available on website. """
        self.ensure_one()
        if self.sudo().team_id.website_published and self.env.user.share:
            try:
                self.check_access_rule('read')
            except exceptions.AccessError:
                pass
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/ticket/%s' % self.id,
                    'target': 'self',
                    'res_id': self.id,
                }
        return super(HelpdeskTicket, self).get_access_action()

    @api.multi
    def _notification_recipients(self, message, groups):
        groups = super(HelpdeskTicket, self)._notification_recipients(message, groups)

        self.ensure_one()
        if self.team_id.website_published:
            for group_name, group_method, group_data in groups:
                group_data['has_button_access'] = True

        return groups


class HelpdeskTeam(models.Model):
    _name = "helpdesk.team"
    _inherit = ['helpdesk.team', 'website.published.mixin']

    website_rating_url = fields.Char('URL to Submit Issue', readonly=True, compute='_compute_website_rating_url')

    def _compute_website_rating_url(self):
        for team in self.filtered(lambda team: team.name and team.use_website_helpdesk_rating and team.id):
            team.website_rating_url = '/helpdesk/rating/%s' % slug(team)

    @api.multi
    def _compute_website_url(self):
        super(HelpdeskTeam, self)._compute_website_url()
        for team in self:
            team.website_url = "/helpdesk/%s" % slug(team)

    @api.onchange('use_website_helpdesk_form', 'use_website_helpdesk_forum', 'use_website_helpdesk_slides')
    def _onchange_use_website_helpdesk(self):
        if not (self.use_website_helpdesk_form or self.use_website_helpdesk_forum or self.use_website_helpdesk_slides) and self.website_published:
            self.website_published = False

    @api.multi
    def action_view_all_rating(self):
        """ Override this method without calling parent to redirect to rating website team page """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Redirect to the Website Helpdesk Rating Page",
            'target': 'self',
            'url': "/helpdesk/rating/%s" % (self.id,)
        }
