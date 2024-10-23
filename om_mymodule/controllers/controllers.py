# -*- coding: utf-8 -*-
from odoo import http

# class OmMymodule(http.Controller):
#     @http.route('/om_mymodule/om_mymodule/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/om_mymodule/om_mymodule/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('om_mymodule.listing', {
#             'root': '/om_mymodule/om_mymodule',
#             'objects': http.request.env['om_mymodule.om_mymodule'].search([]),
#         })

#     @http.route('/om_mymodule/om_mymodule/objects/<model("om_mymodule.om_mymodule"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('om_mymodule.object', {
#             'object': obj
#         })