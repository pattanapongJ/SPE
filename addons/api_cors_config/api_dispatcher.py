# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo.http import request
from odoo.addons.api_framework_base.api_dispatcher import APIRequest, ApiValues

ALL_ORIGINS = '*'

def remove_cors_headers_conf(self, response):
    response.headers.remove('Access-Control-Allow-Origin')
    response.headers.remove('Access-Control-Allow-Methods')
    return response

def manage_cors_headers_conf(self, response):
    if request.endpoint.routing.get('cors') == 'api':
        if self.api_record.get('allowed_origins'):
            allowed_origins = [x.strip().strip('/') for x in self.api_record.get('allowed_origins').split(',')]
            if ALL_ORIGINS in allowed_origins:
                response.headers.set('Access-Control-Allow-Origin', ALL_ORIGINS)
                if request.endpoint.routing.get('methods'):
                    methods = ', '.join(request.endpoint.routing['methods'])
                    response.headers.set('Access-Control-Allow-Methods', methods)
                return response
            elif request.httprequest.headers.get('origin') in allowed_origins:
                response.headers.set('Access-Control-Allow-Origin', 
                                                    request.httprequest.headers.get('origin'))
                if request.endpoint.routing.get('methods'):
                    methods = ', '.join(request.endpoint.routing['methods'])
                    response.headers.set('Access-Control-Allow-Methods', methods)
                return response
            else:
                response = self.remove_cors_headers(response)
                return response
        else:
            response = self.remove_cors_headers(response)
            return response
    else:
        response = self.remove_cors_headers(response)
        return response

def get_cors_related_api_values(cls, api_record):
    if not api_record:
            return None
    values = {
        'id': api_record.id,
        'base_endpoint': api_record.base_endpoint,
        'api_type': api_record.api_type,
        'authentication_type': api_record.authentication_type,
        'resource_control_type': api_record.resource_control_type,
        'error_debug': api_record.error_debug,
        'error_detail': api_record.error_detail,
        'page_size': api_record.page_size,
    }
    if hasattr(api_record, 'allowed_origins'):
        values['allowed_origins'] = api_record.allowed_origins
    return values

ApiValues.get_api_values = get_cors_related_api_values
APIRequest.remove_cors_headers = remove_cors_headers_conf
APIRequest.manage_cors_headers = manage_cors_headers_conf
