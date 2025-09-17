# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from datetime import datetime
from odoo import models
from odoo.api import Environment
from odoo.http import WebRequest, request
from odoo.exceptions import AccessDenied

ACCESS_TOKEN_LENGTH = 64


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def verify_api_key(cls, apikey, su=None):
        api_record = request.env['easy.api'].sudo().browse(request.api_record['id'])
        api_key = api_record.api_key_ids.filtered_domain(
            [('apikey', '=', apikey)])
        if len(api_key) != 1:
            raise AccessDenied('Access Denied')
        current_time = datetime.now().replace(microsecond=0)

        if current_time > api_key.expiry:
            raise AccessDenied('Access Denied')
        user = api_key.user_id
        request._env = Environment(request.cr, user.id, request.context, su)

    @classmethod
    def _auth_method_apikey(cls, su=None):
        if request.httprequest.headers.get('x-api-key'):
            apikey = request.httprequest.headers.get('x-api-key')
            cls.verify_api_key(apikey, su=su)
        else:
            raise AccessDenied('Access Denied')
