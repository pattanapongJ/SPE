# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from werkzeug.routing import UnicodeConverter
from odoo import models
from odoo.api import Environment
from odoo.http import request


class ApiConverter(UnicodeConverter):
    pass


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_api(cls):
        super()._auth_method_api()
        if request.resource_control_type == 'custom_access':
            getattr(cls, f'_auth_method_{request.auth_type}')()
            api_record = request.env['easy.api'].sudo().browse(request.api_record['id'])
            if api_record.resource_control_id:
                invokeuser = api_record.resource_control_id.user_id.id
            else:
                invokeuser = None
            request._env = Environment(request.cr, invokeuser, request.context)
        elif request.resource_control_type == False:
            raise Exception()
