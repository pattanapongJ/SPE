# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api
from odoo.http import request
from odoo.http import Controller as JsonAPIController
from odoo.http import route as jsonapiRoute
from odoo.addons.easy_jsonapi.models import easy_jsonapi

PUBLIC_HELP = '''Enabling this option allows you to define public methods with json:api dynamic calls.

You can define public method as following.


class YourPublicJsonAPI(models.AbstractModel):
    _inherit = 'easy.jsonapi.public.methods'

    @classmethod
    def allowed_public(cls):
        res = super().allowed_public()
        res.extend(['demo'])  # define your public methods
        return res

    @classmethod
    def demo(self, query, response):
        """This is your custom public method works dynamic with configured apis."""
        response.jsonapi_data = {
            'result': 'Demo Successful',
        }
        return response
'''

class EasyApi(models.Model):
    _inherit = 'easy.api'

    allow_public_jsonapi = fields.Boolean('Allow Public JsonAPI (Basic)', tracking=True, help=PUBLIC_HELP)

    @api.onchange('authentication_type', 'api_type')
    def _onchange_public_jsonapi_basic(self):
        for rec in self:
            if rec.authentication_type != 'basic' or rec.api_type != 'jsonapi':
                rec.allow_public_jsonapi = False


class SignUpEasyJsonApi(models.TransientModel):
    _inherit = 'easy.jsonapi'

    @classmethod
    def serve_public(cls):
        if request.httprequest.method != 'POST':
            raise Exception('Not Found')
        if not (request.env.user and request.env.user._is_public):
            raise Exception('Not Allowed')

        query = easy_jsonapi.JsonAPIQuery(request=request)
        query.parse_request()
        response = easy_jsonapi.JsonAPIResponse(meta={"version": "1.1"})
        public_method = query.model
        jsonapiPublicObj = request.env['easy.jsonapi.public.methods']
        if hasattr(jsonapiPublicObj, public_method):
            return getattr(jsonapiPublicObj, public_method)(query, response)
        else:
            raise Exception('Method Not Found')


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _generate_routing_rules(cls, modules, converters):
        if not request:
            yield from super()._generate_routing_rules(modules, converters)
            return
        else:
            all_custom_apis = request.env['easy.api'].sudo().search([('api_type', '=', 'jsonapi'), ('allow_public_jsonapi', '=', True)])
            public_endpoints_to_register = request.env['easy.jsonapi.public.methods'].allowed_public()
            all_endpoints = []
            for api in all_custom_apis:
                all_endpoints.extend(
                    [f'/{api.base_endpoint}/{public_point}' for public_point in public_endpoints_to_register]
                )
            for url, endpoint, routing in super()._generate_routing_rules(modules, converters):
                if url == '/_jsonapi_dynamic_api_route_public':
                    for endpoint_url in all_endpoints:
                       yield endpoint_url, endpoint, routing
                else:
                    yield url, endpoint, routing


class JsonAPIPublic(JsonAPIController):
    @jsonapiRoute(['/_jsonapi_dynamic_api_route_public'], auth='public', csrf=False, methods=['POST'], cors='api', save_session=False)
    def publicJsonApiGetController(self):
        return request.env['easy.jsonapi'].serve_public()
