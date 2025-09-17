# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api

class EasyApiAuthOAuth2(models.Model):
    _inherit = 'easy.api'

    authentication_type = fields.Selection(selection_add=[('oauth2','Using OAuth 2.0')])
    oauth2_provider_ids = fields.Many2many('auth.oauth.provider', string='OAuth Providers',
                                           domain=[('api_allowed', '=', True)])
    oauth2_redirect_link = fields.Text(string='Redirect Link', compute='_compute_oauth2_redirect_link')
    api_user_ids = fields.One2many('api.user', 'easy_api_id')

    @api.depends('authentication_type')
    def _compute_authentication_type_help(self):
        super()._compute_authentication_type_help()
        for rec in self:
            if rec.authentication_type == 'oauth2':
                help_msg = ('"<b>Authentication Type</b>: This field describe which type of '
                            'authentication method you are going to use, Currently it is '
                            'OAuth2: OAuth 2.0 resource API access ensures that access '
                            'to protected resources is securely managed, allowing applications to '
                            'access data by using access-tokens.')
                rec.authentication_type_help = help_msg

    def _compute_oauth2_redirect_link(self):
        for rec in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            rec.oauth2_redirect_link = f'{base_url}/auth/oauth2/callback'
