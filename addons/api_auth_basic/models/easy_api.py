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
you are going to use, Currently it is Basic: use "Authorization" Header and pass value like
"Basic &#60;credentials&#62;" here credentials is base64 encoded string which is user's
username and password that are combined with a colon.
"""

class EasyApiAuthBasic(models.Model):
    _inherit = 'easy.api'

    authentication_type = fields.Selection(selection_add=[('basic','Basic Authentication')])

    @api.depends('authentication_type')
    def _compute_authentication_type_help(self):
        super()._compute_authentication_type_help()
        for rec in self:
            if rec.authentication_type == 'basic':
                rec.authentication_type_help = AUTH_TYPE_HELP
