# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

"""GraphQL Controllers"""
from odoo import http
from odoo.http import request


class GraphQlControllers(http.Controller):

    @http.route(['/_graphql_dynamic_api_route'], auth='api', csrf=False, cors='api', methods=['POST'], save_session=False)
    def graphQlController(self):
        data = request.httprequest.data.decode()
        return request.env['easyapi.graphql'].handle_query(data=data)

