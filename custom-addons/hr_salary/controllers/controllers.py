# -*- coding: utf-8 -*-
from odoo import http

# class HrSalary(http.Controller):
#     @http.route('/hr_salary/hr_salary/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_salary/hr_salary/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_salary.listing', {
#             'root': '/hr_salary/hr_salary',
#             'objects': http.request.env['hr_salary.hr_salary'].search([]),
#         })

#     @http.route('/hr_salary/hr_salary/objects/<model("hr_salary.hr_salary"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_salary.object', {
#             'object': obj
#         })