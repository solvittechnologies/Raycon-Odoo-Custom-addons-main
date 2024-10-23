# -*- coding: utf-8 -*-
from odoo import http

# class ProjectCosting(http.Controller):
#     @http.route('/project_costing/project_costing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/project_costing/project_costing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('project_costing.listing', {
#             'root': '/project_costing/project_costing',
#             'objects': http.request.env['project_costing.project_costing'].search([]),
#         })

#     @http.route('/project_costing/project_costing/objects/<model("project_costing.project_costing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('project_costing.object', {
#             'object': obj
#         })