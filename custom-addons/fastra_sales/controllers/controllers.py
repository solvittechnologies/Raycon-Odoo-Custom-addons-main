# -*- coding: utf-8 -*-
from odoo import http

# class FastraSales(http.Controller):
#     @http.route('/fastra_sales/fastra_sales/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fastra_sales/fastra_sales/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fastra_sales.listing', {
#             'root': '/fastra_sales/fastra_sales',
#             'objects': http.request.env['fastra_sales.fastra_sales'].search([]),
#         })

#     @http.route('/fastra_sales/fastra_sales/objects/<model("fastra_sales.fastra_sales"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fastra_sales.object', {
#             'object': obj
#         })