# -*- coding: utf-8 -*-
from odoo import http

# class PrformFastraExtension(http.Controller):
#     @http.route('/prform_fastra_extension/prform_fastra_extension/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prform_fastra_extension/prform_fastra_extension/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('prform_fastra_extension.listing', {
#             'root': '/prform_fastra_extension/prform_fastra_extension',
#             'objects': http.request.env['prform_fastra_extension.prform_fastra_extension'].search([]),
#         })

#     @http.route('/prform_fastra_extension/prform_fastra_extension/objects/<model("prform_fastra_extension.prform_fastra_extension"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prform_fastra_extension.object', {
#             'object': obj
#         })