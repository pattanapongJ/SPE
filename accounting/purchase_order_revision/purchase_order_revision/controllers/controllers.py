# -*- coding: utf-8 -*-
# from odoo import http


# class Odoo(http.Controller):
#     @http.route('/odoo/odoo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odoo/odoo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('odoo.listing', {
#             'root': '/odoo/odoo',
#             'objects': http.request.env['odoo.odoo'].search([]),
#         })

#     @http.route('/odoo/odoo/objects/<model("odoo.odoo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odoo.object', {
#             'object': obj
#         })
