# -*- coding: utf-8 -*-
from odoo import http

# class AnalyticalAccountingExtention(http.Controller):
#     @http.route('/analytical_accounting_extention/analytical_accounting_extention/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/analytical_accounting_extention/analytical_accounting_extention/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('analytical_accounting_extention.listing', {
#             'root': '/analytical_accounting_extention/analytical_accounting_extention',
#             'objects': http.request.env['analytical_accounting_extention.analytical_accounting_extention'].search([]),
#         })

#     @http.route('/analytical_accounting_extention/analytical_accounting_extention/objects/<model("analytical_accounting_extention.analytical_accounting_extention"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('analytical_accounting_extention.object', {
#             'object': obj
#         })