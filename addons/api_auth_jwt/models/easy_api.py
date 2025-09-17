# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api
from odoo.addons.ekika_utils.tools.helpers import generate_keys

AUTH_TYPE_HELP = '''
<b>Authentication Type</b>:
This field describe which type of authentication method you are going to use,
currently it is JWT Authentication: Use this authentication type when you want to use this API with JWT Authentication.
'''

class EasyApiAuthJWT(models.Model):
    _inherit = 'easy.api'

    authentication_type = fields.Selection(selection_add=[('api_jwt','JWT Authentication')])
    # JWT Authentication Settings
    api_jwt_algo = fields.Selection(
        selection=[('HS256','HS256'), ('HS384','HS384'), ('HS512','HS512'), ('RS256','RS256'), ('RS384','RS384'),
                   ('RS512','RS512'), ('ES256','ES256'), ('ES384','ES384'), ('ES512','ES512'), ('PS256','PS256'),
                   ('PS384','PS384'), ('PS512','PS512')],
        default='HS256', string='JWT Algorithm')
    jwt_expiry_time_hours = fields.Float('JWT Expiry Time (in Hours)')
    jwt_secret_key = fields.Text('JWT Secret Key')
    jwt_private_key = fields.Text('JWT Private Key')
    jwt_public_key = fields.Text('JWT Public Key')

    @api.depends('authentication_type')
    def _compute_authentication_type_help(self):
        super()._compute_authentication_type_help()
        for rec in self:
            if rec.authentication_type == 'api_jwt':
                rec.authentication_type_help = AUTH_TYPE_HELP

    def action_update_jwt_keys(self, **kwargs):
        key_values = generate_keys(self.api_jwt_algo)
        if key_values.get('secret_key'):
            self.jwt_secret_key = key_values['secret_key']
        else:
            self.jwt_private_key = key_values['private_key']
            self.jwt_public_key = key_values['public_key']
