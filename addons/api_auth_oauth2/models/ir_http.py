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
from odoo.exceptions import AccessDenied


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def validate_api_token_request(cls, provider, access_token):
        values = request.env['res.users'].sudo()._auth_oauth_validate(provider, access_token)
        return values

    @classmethod
    def _auth_method_oauth2(cls, su=None):
        """
        This method is used to verify access_token and provide resource access
        """
        auth_header = request.httprequest.headers.get('Authorization')
        if auth_header:
            authorization = auth_header.split()
            if authorization[0] == 'Bearer':
                token = authorization[1]
                api_record = request.env['easy.api'].sudo().browse(request.api_record['id'])
                user_rec = api_record.api_user_ids\
                           .filtered_domain([('access_token', '=', token)]).user_id
                if not user_rec:
                    raise AccessDenied({'error': 'invalid_request'})
                try:
                    values = cls.validate_api_token_request(user_rec.oauth_provider_id.id, token)
                except Exception as exc:
                    raise AccessDenied({'error': 'invalid_request'}) from exc
                if str(values['user_id']) != str(user_rec.oauth_uid):
                    raise AccessDenied({'error': 'invalid_request'})
                else:
                    request._env = Environment(request.cr, user_rec.id, request.context, su)
            else:
                raise AccessDenied({'error': 'invalid_request'})
        else:
            raise AccessDenied('Access Denied')

