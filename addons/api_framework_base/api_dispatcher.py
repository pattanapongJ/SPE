# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

import odoo
from werkzeug.exceptions import NotFound
from werkzeug.wrappers import Response
from odoo.api import Environment
from odoo.http import WebRequest, request
from odoo.http import Root
from .exceptions import UnsupportedMediaType

from abc import ABC, abstractmethod

# The request mimetypes that transport JSON in their body.
SUPPORTED_API_MIMETYPES = ('application/json', 'application/vnd.api+json', 'application/json-rpc')
JSONAPI_MIMETYPE = ('application/vnd.api+json')

CORS_MAX_AGE = 60 * 60 * 24


class EasyAPI(ABC):
    api_type: str

    # main api types. i.e. jsonapi, graphql etc.
    _apis = {}

    # Holds the record relevent to the API call.
    api_record = None

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        EasyAPI._apis[cls.api_type] = cls

    def __init__(self, api_record):
        self.api_record = api_record

    @classmethod
    @abstractmethod
    def confirm_mimetype(cls, mimetype):
        """Determine if the current request is compatible with this api."""

    def pre_process(self):
        """Prepare the process so it can be easy served by subsequent api."""
        pass

    @abstractmethod
    def process_request(self, endpoint, args):
        """
        Extract the params from the request's body and call the endpoint.
        This method needs to be overridden by API implementor to process
        relevent endpoints to them.
        """

    def post_process(self, response):
        """Prepare the process so it can be easy served by subsequent api."""
        pass


class SessionExpiredException(Exception):
    pass


class APIRequest(WebRequest):
    _request_type = "http"
    _is_easy_api_type = True

    def guessBaseEndpoint(self):
        path = request.httprequest.path
        pathParts = path.split('/')
        if path.startswith('/') and len(pathParts) >= 2:
            matchBaseEndpoint = pathParts[1]
        elif len(pathParts) >= 1:
            matchBaseEndpoint = pathParts[0]
        else:
            matchBaseEndpoint = path
        return matchBaseEndpoint

    def get_api_record(self):
        if self.api_record:
            return self.api_record
        else:
            api_records = request.env['easy.api'].sudo().search(
                [('base_endpoint', '=', self.guessBaseEndpoint()),('state', '=', 'active')])
            if not api_records:
                raise NotFound
            if api_records and len(api_records) != 1:
                raise Exception('Too many API found.')
            self.api_record = api_records[0]
            return self.api_record

    def __init__(self, httprequest, api_record):
        super(APIRequest, self).__init__(httprequest=httprequest)
        self.params = {}
        self.api_record = api_record
        self.base_endpoint = self.api_record['base_endpoint']
        self.auth_type = self.api_record['authentication_type']
        self.resource_control_type = self.api_record['resource_control_type']
        api_cls = EasyAPI._apis[api_record['api_type']]
        # ToDo: Allow config of CORS in API.
        if not api_cls.confirm_mimetype(httprequest):
            raise UnsupportedMediaType
        self.api = api_cls(self.api_record)

    def _is_cors_preflight(self, endpoint):
        return request.httprequest.method == 'OPTIONS'

    def manage_cors_headers(self, response):
        """
        This method is going to be used for add/remove headers related to CORS. 
        """
        if response.headers.get('Access-Control-Allow-Origin') == 'api':
            response.headers.remove('Access-Control-Allow-Origin')
            response.headers.remove('Access-Control-Allow-Methods')
        return response

    def dispatch(self):
        """Process Request with Help of API handler."""
        response = self.api.process_request()
        response = self.manage_cors_headers(response)
        return response

    def _handle_exception(self, exception):
        try:
            return super(APIRequest, self)._handle_exception(exception)
        except Exception:
            return self.api.handle_error(exception)

    def set_response_cookie(self, response, cookies):
        for key, val in cookies.items():
            response.set_cookie(key, val)

    def make_response(self, data, headers=None, cookies=None):
        response = Response(data, headers=headers)
        if cookies:
            self.set_response_cookie(response, cookies)
        return response

orignal_get_request = Root.get_request

def guessBaseEndpoint(path):
    pathParts = path.split('/')
    if path.startswith('/') and len(pathParts) >= 2:
        matchBaseEndpoint = pathParts[1]
    elif len(pathParts) >= 1:
        matchBaseEndpoint = pathParts[0]
    else:
        matchBaseEndpoint = path
    return matchBaseEndpoint

#add This in version-15
def new_condition_get_request(cls, httprequest):
    path_info = httprequest.path
    db = httprequest.session.db
    # ToDo: Move this somewhere around registry loading procedure
    # should be done during service restart and when routes are update in database
    api_record = None
    if db and odoo.service.db.exp_db_exist(db):
        registry = odoo.registry(db).check_signaling()
        with registry.cursor() as cr:
            env = Environment(cr, odoo.SUPERUSER_ID, {})
            # ToDo: Isolate our api request before creating environment
            # This method have been patched where database does not have this module installed
            if 'easy.api' in env:
                api_record = env['easy.api'].sudo().search(
                    [('base_endpoint', '=', guessBaseEndpoint(path_info)),('state', '=', 'active')])
                api_vals = ApiValues().get_api_values(api_record)
            else:
                return orignal_get_request(cls, httprequest)
    if api_record:
        return APIRequest(httprequest, api_record=api_vals)
    else:
        return orignal_get_request(cls, httprequest)

class ApiValues:
    @classmethod
    def get_api_values(cls, api_record):
        if not api_record:
            return None
        return {
            'id': api_record.id,
            'base_endpoint': api_record.base_endpoint,
            'api_type': api_record.api_type,
            'authentication_type': api_record.authentication_type,
            'resource_control_type': api_record.resource_control_type,
            'error_debug': api_record.error_debug,
            'error_detail': api_record.error_detail,
            'page_size': api_record.page_size,
        }

Root.get_request = new_condition_get_request
