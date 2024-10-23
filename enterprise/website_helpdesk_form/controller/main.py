# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request

from odoo.addons.website_helpdesk.controllers.main import WebsiteForm


class WebsiteForm(WebsiteForm):

    @http.route('''/helpdesk/<model("helpdesk.team", "[('use_website_helpdesk_form','=',True)]"):team>/submit''', type='http', auth="public", website=True)
    def website_helpdesk_form(self, team, **kwargs):
        default_values = {}
        if request.env.user.partner_id != request.env.ref('base.public_partner'):
            default_values['name'] = request.env.user.partner_id.name
            default_values['email'] = request.env.user.partner_id.email
        return request.render("website_helpdesk_form.ticket_submit", {'team': team, 'default_values': default_values})
