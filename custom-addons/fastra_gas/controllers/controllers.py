# -*- coding: utf-8 -*-
from odoo import http

# class FastraGas(http.Controller):
#     @http.route('/fastra_gas/fastra_gas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fastra_gas/fastra_gas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fastra_gas.listing', {
#             'root': '/fastra_gas/fastra_gas',
#             'objects': http.request.env['fastra_gas.fastra_gas'].search([]),
#         })

#     @http.route('/fastra_gas/fastra_gas/objects/<model("fastra_gas.fastra_gas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fastra_gas.object', {
#             'object': obj
#         })