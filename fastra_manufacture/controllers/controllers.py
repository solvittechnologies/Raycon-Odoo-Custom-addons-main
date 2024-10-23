# -*- coding: utf-8 -*-
from odoo import http

# class FastraManufacture(http.Controller):
#     @http.route('/fastra_manufacture/fastra_manufacture/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fastra_manufacture/fastra_manufacture/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fastra_manufacture.listing', {
#             'root': '/fastra_manufacture/fastra_manufacture',
#             'objects': http.request.env['fastra_manufacture.fastra_manufacture'].search([]),
#         })

#     @http.route('/fastra_manufacture/fastra_manufacture/objects/<model("fastra_manufacture.fastra_manufacture"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fastra_manufacture.object', {
#             'object': obj
#         })