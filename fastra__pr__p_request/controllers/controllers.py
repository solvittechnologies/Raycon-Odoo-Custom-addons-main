# -*- coding: utf-8 -*-
from odoo import http

# class FastraPrPRequest(http.Controller):
#     @http.route('/fastra__pr__p_request/fastra__pr__p_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fastra__pr__p_request/fastra__pr__p_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fastra__pr__p_request.listing', {
#             'root': '/fastra__pr__p_request/fastra__pr__p_request',
#             'objects': http.request.env['fastra__pr__p_request.fastra__pr__p_request'].search([]),
#         })

#     @http.route('/fastra__pr__p_request/fastra__pr__p_request/objects/<model("fastra__pr__p_request.fastra__pr__p_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fastra__pr__p_request.object', {
#             'object': obj
#         })