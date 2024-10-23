# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.website_form.controllers.main import WebsiteForm


class website_account(website_account):
    @http.route()
    def account(self, **kw):
        response = super(website_account, self).account()
        user = request.env.user
        tickets_count = request.env['helpdesk.ticket'].sudo().search_count(['|', ('user_id', '=', user.id), ('partner_id', '=', user.partner_id.id)])
        response.qcontext.update({'tickets': tickets_count})
        return response

    @http.route(['/my/tickets'], type='http', auth="user", website=True)
    def my_helpdesk_tickets(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        tickets = request.env['helpdesk.ticket'].sudo().search(['|', ('user_id', '=', user.id), ('partner_id', '=', user.partner_id.id)])
        values.update({
            'tickets': tickets,
            'default_url': '/my/tickets',
        })
        return request.render("website_helpdesk.portal_helpdesk_ticket", values)


class WebsiteForm(WebsiteForm):

    def get_helpdesk_team_data(self, team, search=None):
        return {'team': team}

    @http.route(['/helpdesk/', '/helpdesk/<model("helpdesk.team"):team>'], type='http', auth="public", website=True)
    def website_helpdesk_teams(self, team=None, **kwargs):
        search = kwargs.get('search')
        # For breadcrumb index: get all team
        teams = request.env['helpdesk.team'].search(['|', '|', ('use_website_helpdesk_form', '=', True), ('use_website_helpdesk_forum', '=', True), ('use_website_helpdesk_slides', '=', True)], order="id asc")
        if not request.env.user.has_group('helpdesk.group_helpdesk_manager'):
            teams = teams.filtered(lambda team: team.website_published)
        if not teams:
            return request.render("website_helpdesk.not_published_any_team")
        result = self.get_helpdesk_team_data(team or teams[0], search=search)
        # For breadcrumb index: get all team
        result['teams'] = teams
        return request.render("website_helpdesk.team", result)

    @http.route([
        "/helpdesk/ticket/<int:ticket_id>",
        "/helpdesk/ticket/<int:ticket_id>/<token>"
    ], type='http', auth="public", website=True)
    def tickets_followup(self, ticket_id, token=None):
        Ticket = False
        if token:
            Ticket = request.env['helpdesk.ticket'].sudo().search([('id', '=', ticket_id), ('access_token', '=', token)])
        else:
            Ticket = request.env['helpdesk.ticket'].browse(ticket_id)
        if not Ticket:
            return request.render('website.404')
        return request.render("website_helpdesk.tickets_followup", {'ticket': Ticket})

    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        if request.params.get('partner_email'):
            Partner = request.env['res.partner'].sudo().search([('email', '=', kwargs.get('partner_email'))], limit=1)
            if Partner:
                request.params['partner_id'] = Partner.id
        return super(WebsiteForm, self).website_form(model_name, **kwargs)


class WebsiteHelpdesk(http.Controller):

    @http.route(['/helpdesk/rating/'], type='http', auth="public", website=True)
    def index(self, **kw):
        teams = request.env['helpdesk.team'].sudo().search([('use_rating', '=', True), ('use_website_helpdesk_rating', '=', True)])
        values = {'teams': teams}
        return request.render('website_helpdesk.index', values)

    @http.route(['/helpdesk/rating/<model("helpdesk.team"):team>'], type='http', auth="public", website=True)
    def page(self, team, project_id=None, **kw):
        user = request.env.user
        # to avoid giving any access rights on helpdesk team to the public user, let's use sudo
        # and check if the user should be able to view the team (team managers only if it's not published or has no rating)
        if not (team.use_rating and team.use_website_helpdesk_rating) and not user.sudo(user).has_group('helpdesk.group_helpdesk_manager'):
            raise NotFound()
        tickets = request.env['helpdesk.ticket'].sudo().search([('team_id', '=', team.id)])
        domain = [
            ('res_model', '=', 'helpdesk.ticket'), ('res_id', 'in', tickets.ids),
            ('consumed', '=', True), ('rating', '>=', 1),
        ]
        ratings = request.env['rating.rating'].search(domain, order="id desc", limit=100)

        yesterday = (datetime.date.today()-datetime.timedelta(days=-1)).strftime('%Y-%m-%d 23:59:59')
        stats = {}
        for x in (7, 30, 90):
            todate = (datetime.date.today()-datetime.timedelta(days=x)).strftime('%Y-%m-%d 00:00:00')
            domdate = domain + [('create_date', '<=', yesterday), ('create_date', '>=', todate)]
            stats[x] = {1: 0, 5: 0, 10: 0}
            rating_stats = request.env['rating.rating'].read_group(domdate, [], ['rating'])
            total = reduce(lambda x, y: y['rating_count']+x, rating_stats, 0)
            for rate in rating_stats:
                stats[x][rate['rating']] = (rate['rating_count'] * 100) / total
        values = {
            'team': team,
            'ratings': ratings,
            'stats': stats,
        }
        return request.render('website_helpdesk.team_rating_page', values)
