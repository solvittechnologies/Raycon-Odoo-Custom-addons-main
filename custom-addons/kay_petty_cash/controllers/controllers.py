# -*- coding: utf-8 -*-
from odoo import http

# class KayPettyCash(http.Controller):
#     @http.route('/kay_petty_cash/kay_petty_cash/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kay_petty_cash/kay_petty_cash/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('kay_petty_cash.listing', {
#             'root': '/kay_petty_cash/kay_petty_cash',
#             'objects': http.request.env['kay_petty_cash.kay_petty_cash'].search([]),
#         })

#     @http.route('/kay_petty_cash/kay_petty_cash/objects/<model("kay_petty_cash.kay_petty_cash"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kay_petty_cash.object', {
#             'object': obj
#         })