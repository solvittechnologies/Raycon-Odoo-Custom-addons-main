# -*- coding: utf-8 -*-
from odoo import http

# class FastarMaterialRequest(http.Controller):
#     @http.route('/fastar_material_request/fastar_material_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fastar_material_request/fastar_material_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fastar_material_request.listing', {
#             'root': '/fastar_material_request/fastar_material_request',
#             'objects': http.request.env['fastar_material_request.fastar_material_request'].search([]),
#         })

#     @http.route('/fastar_material_request/fastar_material_request/objects/<model("fastar_material_request.fastar_material_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fastar_material_request.object', {
#             'object': obj
#         })