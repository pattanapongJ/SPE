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

    # API Key Setting
    api_key_choice = fields.Selection(
        selection=[('auto','Auto'), ('manual','Manual')],
        default='auto',
        config_parameter='api_auth_apikey.api_key_choice')
