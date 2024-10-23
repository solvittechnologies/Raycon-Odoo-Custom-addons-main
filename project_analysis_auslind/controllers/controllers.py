# -*- coding: utf-8 -*-
from odoo import http

# class ProjectAnalysisAuslind(http.Controller):
#     @http.route('/project_analysis_auslind/project_analysis_auslind/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/project_analysis_auslind/project_analysis_auslind/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('project_analysis_auslind.listing', {
#             'root': '/project_analysis_auslind/project_analysis_auslind',
#             'objects': http.request.env['project_analysis_auslind.project_analysis_auslind'].search([]),
#         })

#     @http.route('/project_analysis_auslind/project_analysis_auslind/objects/<model("project_analysis_auslind.project_analysis_auslind"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('project_analysis_auslind.object', {
#             'object': obj
#         })