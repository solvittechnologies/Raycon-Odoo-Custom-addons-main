# -*- coding: utf-8 -*-
from odoo import http

# class FastraLocationUser(http.Controller):
#     @http.route('/fastra_location_user/fastra_location_user/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fastra_location_user/fastra_location_user/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fastra_location_user.listing', {
#             'root': '/fastra_location_user/fastra_location_user',
#             'objects': http.request.env['fastra_location_user.fastra_location_user'].search([]),
#         })

#     @http.route('/fastra_location_user/fastra_location_user/objects/<model("fastra_location_user.fastra_location_user"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fastra_location_user.object', {
#             'object': obj
#         })