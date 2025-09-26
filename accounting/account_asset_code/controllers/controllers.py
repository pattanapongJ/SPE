# -*- coding: utf-8 -*-
# from odoo import http


# class AccountAssetCode(http.Controller):
#     @http.route('/account_asset_code/account_asset_code/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_asset_code/account_asset_code/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_asset_code.listing', {
#             'root': '/account_asset_code/account_asset_code',
#             'objects': http.request.env['account_asset_code.account_asset_code'].search([]),
#         })

#     @http.route('/account_asset_code/account_asset_code/objects/<model("account_asset_code.account_asset_code"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_asset_code.object', {
#             'object': obj
#         })
