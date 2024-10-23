# -*- coding: utf-8 -*-
from odoo import http

# class FastraInventoryRrExtention(http.Controller):
#     @http.route('/fastra_inventory__rr__extention/fastra_inventory__rr__extention/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fastra_inventory__rr__extention/fastra_inventory__rr__extention/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fastra_inventory__rr__extention.listing', {
#             'root': '/fastra_inventory__rr__extention/fastra_inventory__rr__extention',
#             'objects': http.request.env['fastra_inventory__rr__extention.fastra_inventory__rr__extention'].search([]),
#         })

#     @http.route('/fastra_inventory__rr__extention/fastra_inventory__rr__extention/objects/<model("fastra_inventory__rr__extention.fastra_inventory__rr__extention"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fastra_inventory__rr__extention.object', {
#             'object': obj
#         })