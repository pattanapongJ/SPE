# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models
from odoo import http


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _generate_routing_rules(cls, modules, converters):
        if not http.request:
            yield from super()._generate_routing_rules(modules, converters)
            return
        else:
            all_graphql_apis = http.request.env['easy.api'].sudo().search([('api_type', '=', 'graphql')])
            all_endpoints = [f'/{r.base_endpoint}' for r in all_graphql_apis]

            for url, endpoint, routing in super()._generate_routing_rules(modules, converters):
                if url in ['/_graphql_dynamic_api_route']:
                    for url in all_endpoints:
                        yield url, endpoint, routing
                else:
                    yield url, endpoint, routing
