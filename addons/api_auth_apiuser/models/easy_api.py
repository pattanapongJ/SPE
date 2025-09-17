# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api

AUTH_TYPE_HELP = """
<b>Authentication Type</b>: This field describe which type of authentication method
you are going to use, Currently it is Api User: use "username" and "password" Headers
in http request.
"""

class EasyApiAuthApiUser(models.Model):
    _inherit = 'easy.api'

    authentication_type = fields.Selection(selection_add=[('apiuser','User Credentials')])

    @api.depends('authentication_type')
    def _compute_authentication_type_help(self):
        super()._compute_authentication_type_help()
        for rec in self:
            if rec.authentication_type == 'apiuser':
                rec.authentication_type_help = AUTH_TYPE_HELP
