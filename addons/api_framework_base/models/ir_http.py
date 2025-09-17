# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from werkzeug.exceptions import NotFound
from werkzeug.wrappers import Response
from werkzeug.routing import UnicodeConverter
from odoo import models
from odoo.http import request


class ApiConverter(UnicodeConverter):
    pass


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_converters(cls):
        """Attach API Converter to match dynamic route."""
        return dict(
            super()._get_converters(),
            api=ApiConverter,
        )

    @classmethod
    def _auth_method_api(cls):
        if hasattr(request, 'auth_type'):
            if request.resource_control_type == 'user_based':
                getattr(cls, f'_auth_method_{request.auth_type}')()
            elif request.resource_control_type == 'full_access':
                getattr(cls, f'_auth_method_{request.auth_type}')(su=True)
            elif request.resource_control_type == False:
                raise Exception()
        elif not hasattr(request, 'api_record'):
            raise NotFound()
        else:
            raise Exception()


    @classmethod
    def _dispatch(cls):
        if getattr(request, '_is_easy_api_type', False):
            if request._is_cors_preflight(request.endpoint):
                headers = cls.manage_cors_headers()
                return Response(status=200, headers=headers)
            else:
                return super(IrHttp, cls)._dispatch()
        else:
            return super(IrHttp, cls)._dispatch()

    @classmethod
    def manage_cors_headers(cls):
        return {
            'Access-Control-Max-Age': 60 * 60 * 24,
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization',
        }
