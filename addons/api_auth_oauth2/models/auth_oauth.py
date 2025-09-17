# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import fields, models

class EasyApiAuthOAuthProvider(models.Model):
    _inherit = 'auth.oauth.provider'

    api_allowed = fields.Boolean(string='Allowed For Api')
    client_secret = fields.Text(string='Client Secret')
    token_endpoint = fields.Text(string='Token Endpoint')
    revoke_endpoint = fields.Text(string='Revocation Endpoint')
