# -*- coding: utf-8 -*-
from odoo import http

# class PurchaseRequest(http.Controller):
#     @http.route('/purchase_request/purchase_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_request/purchase_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_request.listing', {
#             'root': '/purchase_request/purchase_request',
#             'objects': http.request.env['purchase_request.purchase_request'].search([]),
#         })

#     @http.route('/purchase_request/purchase_request/objects/<model("purchase_request.purchase_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_request.object', {
#             'object': obj
#         })