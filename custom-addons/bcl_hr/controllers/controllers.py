# -*- coding: utf-8 -*-
from odoo import http

# class Blc(http.Controller):
#     @http.route('/bcl_hr/bcl_hr/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bcl_hr/bcl_hr/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bcl_hr.listing', {
#             'root': '/bcl_hr/bcl_hr',
#             'objects': http.request.env['bcl_hr.bcl_hr'].search([]),
#         })

#     @http.route('/bcl_hr/bcl_hr/objects/<model("bcl_hr.bcl_hr"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bcl_hr.object', {
#             'object': obj
#         })