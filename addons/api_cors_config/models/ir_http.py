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

ALL_ORIGINS = '*'

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def manage_cors_headers(cls):
        headers = {
            'Access-Control-Max-Age': 60 * 60 * 24,
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization',
        }
        if request.api_record.get('allowed_origins'):
            allowed_origins = [x.strip().strip('/') for x in request.api_record.get('allowed_origins').split(',')]
            if ALL_ORIGINS in allowed_origins:
                headers['Access-Control-Allow-Origin'] = ALL_ORIGINS
                headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE'
                headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization, x-api-key'
                return headers
            elif request.httprequest.headers.get('origin') in allowed_origins:
                headers['Access-Control-Allow-Origin'] = request.httprequest.headers.get('origin')
                headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE'
                headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization, x-api-key'
                return headers
            else:
                return headers
        else:
            return headers
