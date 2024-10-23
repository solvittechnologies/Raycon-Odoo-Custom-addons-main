# -*- coding: utf-8 -*-
from odoo import http

# class FfastraMaterialRequest(http.Controller):
#     @http.route('/ffastra_material_request/ffastra_material_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ffastra_material_request/ffastra_material_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ffastra_material_request.listing', {
#             'root': '/ffastra_material_request/ffastra_material_request',
#             'objects': http.request.env['ffastra_material_request.ffastra_material_request'].search([]),
#         })

#     @http.route('/ffastra_material_request/ffastra_material_request/objects/<model("ffastra_material_request.ffastra_material_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ffastra_material_request.object', {
#             'object': obj
#         })