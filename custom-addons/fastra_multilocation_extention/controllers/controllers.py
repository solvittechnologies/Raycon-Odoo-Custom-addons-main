# -*- coding: utf-8 -*-
from odoo import http

# class PoshMultilocation(http.Controller):
#     @http.route('/posh_multilocation/posh_multilocation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/posh_multilocation/posh_multilocation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('posh_multilocation.listing', {
#             'root': '/posh_multilocation/posh_multilocation',
#             'objects': http.request.env['posh_multilocation.posh_multilocation'].search([]),
#         })

#     @http.route('/posh_multilocation/posh_multilocation/objects/<model("posh_multilocation.posh_multilocation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('posh_multilocation.object', {
#             'object': obj
#         })