# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api

AUTH_TYPE_HELP = '''
<b>Authentication Type</b>:
This field describe which type of authentication method you are going to use,
currently it is Public User: Use this authentication type when you want to use this API with public user.
'''

class EasyApiAuthPublic(models.Model):
    _inherit = 'easy.api'

    authentication_type = fields.Selection(selection_add=[('api_public','Public User')])

    @api.depends('authentication_type')
    def _compute_authentication_type_help(self):
        super()._compute_authentication_type_help()
        for rec in self:
            if rec.authentication_type == 'public':
                rec.authentication_type_help = AUTH_TYPE_HELP

    @api.onchange('authentication_type', 'resource_control_type')
    def _onchange_auth_access_type(self):
        for rec in self:
            if rec.authentication_type == 'api_public' and rec.resource_control_type == 'full_access':
                return {
                    'warning': {
                        'title': 'Warning: Security Risk Detected',
                        'message': '''
You are configuring an API with Public User Authentication and Not Using User Based Access. This grants access to sensitive operations, posing risks like:

    * Unauthorized Data Access
    * System Exploits
    * Compliance Violations

Recommendations:

    * Use Authenticated Access with proper permissions like User Based Access.
    * Avoid Sudo operations unless necessary.
    * Well configure personalized access based on your certain needs.

By proceeding, you accept responsibility for any risks or misuse.'''
                    }
                }
