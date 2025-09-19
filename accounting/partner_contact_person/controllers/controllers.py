# -*- coding: utf-8 -*-
# from odoo import http


# class Addons(http.Controller):
#     @http.route('/addons/addons/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/addons/addons/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('addons.listing', {
#             'root': '/addons/addons',
#             'objects': http.request.env['addons.addons'].search([]),
#         })

#     @http.route('/addons/addons/objects/<model("addons.addons"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('addons.object', {
#             'object': obj
#         })
