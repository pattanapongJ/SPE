# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import fields, models

class EasyApiUser(models.Model):
    _name = 'api.user'
    _description = 'API User'

    client_user_id = fields.Text(string="Client User Id")
    user_id = fields.Many2one('res.users', string="User")
    provider_id = fields.Many2one('auth.oauth.provider', string="OAuth Provider")
    access_token = fields.Text(string='Access Token', readonly=True)
    refresh_token = fields.Text(string='Refresh Token', readonly=True)
    easy_api_id = fields.Many2one('easy.api', 'API', readonly=True, ondelete='cascade')
