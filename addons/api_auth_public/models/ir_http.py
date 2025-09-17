# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models
from odoo.http import request
from odoo.api import Environment


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_api_public(cls, su=None):
        public_user = request.env.ref('base.public_user')
        if su:
            request._env = Environment(request.cr, public_user.id, request.context, su)
        else:
            request._env = Environment(request.cr, public_user.id, request.context)
