# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api


AUTH_TYPE_HELP = """
<b>Authentication Type</b>:
This field describe which type of authentication method you are going to use,
currently it is Api Key: Generate API-key for particular user and pass
that API key will be used in "x-api-key" header of http request.
"""


class EasyApiAuthApiKey(models.Model):
    _inherit = 'easy.api'

    authentication_type = fields.Selection(
        selection_add=[('apikey','User\'s API Key')],
        default='apikey')
    api_key_ids = fields.One2many('api.auth.apikey', 'easy_api_id')

    @api.depends('authentication_type')
    def _compute_authentication_type_help(self):
        super()._compute_authentication_type_help()
        for rec in self:
            if rec.authentication_type == 'apikey':
                rec.authentication_type_help = AUTH_TYPE_HELP

