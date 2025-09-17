# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from odoo import models
from odoo import http
from odoo.http import request
from odoo.api import Environment
from odoo.exceptions import AccessDenied
from ..utils import SYMMETRIC_ALGORITHMS, ASYMMETRIC_ALGORITHMS


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_api_jwt(cls, su=None):
        token = request.httprequest.headers.get('Authorization')
        if not token:
            raise AccessDenied('Access Denied')
        if token:
            token = token.split(" ")[1]  # Remove 'Bearer' prefix
            if not token:
                raise AccessDenied('Access Denied')
        try:
            payload = cls.verify_jwt_token(token)
            request._env = Environment(request.cr, payload['sub'], request.context, su)
        except Exception as exc:
            raise exc

    @classmethod
    def verify_jwt_token(cls, token):
        """ Verify JWT token and return the payload if valid """
        try:
            request.easy_api_rec = request.env['easy.api'].sudo().browse(request.api_record['id'])
            jwt_algo = cls.get_jwt_algorithm()
            if jwt_algo in SYMMETRIC_ALGORITHMS:
                payload = cls.verify_symmetric_jwt_algo(token, jwt_algo)
            elif jwt_algo in ASYMMETRIC_ALGORITHMS:
                payload = cls.verify_asymmetric_jwt_algo(token, jwt_algo)
            return payload
        except jwt.ExpiredSignatureError:
            raise AccessDenied("Token has expired")
        except jwt.InvalidTokenError:
            raise AccessDenied("Invalid token")
        except Exception as exc:
            raise AccessDenied("Access Denied")

    @classmethod
    def verify_symmetric_jwt_algo(cls, token, jwt_algo):
        secret_key = cls.get_jwt_secret_key()
        payload = jwt.decode(token, secret_key, algorithms=[jwt_algo])
        return payload

    @classmethod
    def verify_asymmetric_jwt_algo(cls, token, jwt_algo):
        jwt_public_key = cls.get_jwt_public_key()
        public_key = load_pem_public_key(jwt_public_key.encode('utf-8'), backend=default_backend())
        payload = jwt.decode(token, public_key, algorithms=[jwt_algo])
        return payload

    @classmethod
    def get_jwt_algorithm(cls):
        return request.easy_api_rec.api_jwt_algo

    @classmethod
    def get_jwt_public_key(cls):
        return request.easy_api_rec.jwt_public_key

    @classmethod
    def get_jwt_secret_key(cls):
        return request.easy_api_rec.jwt_secret_key

    @classmethod
    def _generate_routing_rules(cls, modules, converters):
        if not http.request:
            yield from super()._generate_routing_rules(modules, converters)
            return
        else:
            all_custom_apis = http.request.env['easy.api'].sudo().search([('authentication_type', '=', 'api_jwt')])
            all_endpoints = [f'/{r.base_endpoint}/api/jwt/auth/login' for r in all_custom_apis]

            for url, endpoint, routing in super()._generate_routing_rules(modules, converters):
                if url in ['/_api_jwt_user_login']:
                    for url in all_endpoints:
                        yield url, endpoint, routing
                else:
                    yield url, endpoint, routing
