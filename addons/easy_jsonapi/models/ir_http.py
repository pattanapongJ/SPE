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
            all_custom_apis = http.request.env['easy.api'].sudo().search([('api_type', '=', 'jsonapi')])
            all_endpoints = [f'/{r.base_endpoint}/<path:uri>' for r in all_custom_apis]
            all_export_endpoints = [f'/{r.base_endpoint}/export' for r in all_custom_apis]
            all_report_endpoints = [f'/{r.base_endpoint}/report' for r in all_custom_apis]

            for url, endpoint, routing in super()._generate_routing_rules(modules, converters):
                if url in ['/_jsonapi_dynamic_api_route']:
                    for url in all_endpoints:
                        yield url, endpoint, routing
                if url in ['/_jsonapi_dynamic_api_route/export']:
                    for url in all_export_endpoints:
                        yield url, endpoint, routing
                if url in ['/_jsonapi_dynamic_api_route/report']:
                    for url in all_report_endpoints:
                        yield url, endpoint, routing
                else:
                    yield url, endpoint, routing

