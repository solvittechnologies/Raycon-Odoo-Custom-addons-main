# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


class website_account_followup(website_account):

    def _get_followup_values(self):
        partner = request.env.user.partner_id
        context_obj = request.env['account.report.context.followup']
        report_obj = request.env['account.followup.report']
        context_id = context_obj.search([('partner_id', '=', int(partner))], limit=1)
        if not context_id:
            # sudo needed to access the report model
            context_id = context_obj.with_context(lang=partner.lang).sudo().create({'partner_id': int(partner)})
        context_id = context_id.sudo() # Needed to see the unreconciled_amls
        lines = report_obj.with_context(lang=partner.lang).get_lines(context_id, public=True)
        return {
            'context': context_id.with_context(lang=partner.lang, public=True),
            'report': report_obj.with_context(lang=partner.lang),
            'lines': lines,
            'mode': 'display',
        }

    @http.route()
    def account(self, **kw):
        response = super(website_account_followup, self).account(**kw)
        rcontext = self._get_followup_values()
        response.qcontext.update({
            'statement_count': len(rcontext['lines'])
        })
        return response

    @http.route(['/my/statement'], type='http', auth="user", website=True)
    def portal_my_statement(self, **kw):
        values = self._prepare_portal_layout_values()
        rcontext = self._get_followup_values()
        values.update(rcontext)
        return request.render("website_portal_followup.portal_my_followup", values)
