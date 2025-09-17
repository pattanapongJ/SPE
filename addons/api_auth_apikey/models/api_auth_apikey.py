# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

import logging

from odoo import api, models, fields
from odoo.addons.ekika_utils.tools import helpers

_logger = logging.getLogger(__name__)


class AuthAPIKey(models.Model):
    """Base Model for apikey based authentication used for APIs."""
    _name = 'api.auth.apikey'
    _description = 'API Key Authentication'

    name = fields.Char(string='APP Name', related='easy_api_id.name', store=True)
    easy_api_id = fields.Many2one('easy.api', 'API', readonly=True, ondelete='cascade')
    apikey = fields.Text(string='API Key', copy=False)
    user_id = fields.Many2one('res.users', string='Invoke User', required=True)
    api_key_choice = fields.Char(readonly=True)
    expiry = fields.Datetime('Expiration Time', required=True)

    _sql_constraints = [
        ('apikey_unique', 'unique (apikey)', 'The apikey of api must be unique!')
    ]

    def get_default_api_key_choice(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'api_auth_apikey.api_key_choice')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        defaults['api_key_choice'] = self.get_default_api_key_choice()
        return defaults

    @api.model_create_multi
    def create(self, vals):
        apikeys = super(AuthAPIKey, self).create(vals)
        for apikey in apikeys:
            if apikey.api_key_choice == 'auto':
                newApiKey = None
                while True:
                    newApiKey = helpers.generate_string()
                    if self.search_count([('apikey', '=', newApiKey)]) == 0:
                        break
                apikey.apikey = newApiKey
        _logger.info('New API Key Generated')
        return apikeys

