# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

"""RestJson Controllers"""
from odoo import http
from odoo.http import request


class RestJsonAPIControllers(http.Controller):

    @http.route(['/_rest_json_dynamic_api_route'], auth='api', csrf=False, cors='api', save_session=False)
    def restJsonAPIController(self):
        return request.env['easy.rest.json'].handle_request()
