# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models
from odoo.api import Environment
from odoo.http import request
from odoo.exceptions import AccessDenied

ACCESS_TOKEN_LENGTH = 64


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def verify_user(cls, username, password, su=None):
        userId = request.env['res.users']._login(
            request.db, username, password, request.env)
        request._env = Environment(request.cr, userId, request.context, su)

    @classmethod
    def _auth_method_apiuser(cls, su=None):
        username = request.httprequest.headers.get('username')
        password = request.httprequest.headers.get('password')
        if username and password:
            cls.verify_user(username, password, su)
        else:
            raise AccessDenied('Please Pass Credentials as per document in Header')
