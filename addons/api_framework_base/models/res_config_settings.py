# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_api_auth_token = fields.Boolean('Token')
    module_api_auth_oauth2 = fields.Boolean('OAuth 2.0')
    module_api_auth_oauth1 = fields.Boolean('OAuth 1.0')
    module_api_auth_openid = fields.Boolean('OpenID')
    module_api_auth_basic = fields.Boolean('Basic')
    module_api_auth_apikey = fields.Boolean('API Key')
    module_api_auth_apiuser = fields.Boolean('API User')

    api_mode = fields.Selection(selection=[('easy', 'Easy'), ('advance', 'Advance')],
                                default='easy', config_parameter='api_framework_base.api_mode')
