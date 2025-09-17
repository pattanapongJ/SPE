# -*- coding: utf-8 -*-
# from odoo import http


# class AccountAssetHolder(http.Controller):
#     @http.route('/account_asset_holder/account_asset_holder/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_asset_holder/account_asset_holder/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_asset_holder.listing', {
#             'root': '/account_asset_holder/account_asset_holder',
#             'objects': http.request.env['account_asset_holder.account_asset_holder'].search([]),
#         })

#     @http.route('/account_asset_holder/account_asset_holder/objects/<model("account_asset_holder.account_asset_holder"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_asset_holder.object', {
#             'object': obj
#         })
