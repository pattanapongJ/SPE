# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

"""
args = {
    'fields[sale.order]': 'name,partner_id',
    'include': 'partner_id',
    'fields[res.partner]': 'name',
    'sort': 'name',
    'filter[amount_total.>]': '1500',
    'filter[amount_total.<]': '2000',
    'page[number]': '3',
    'page[size]': '3',
}

"""
import json
from math import ceil
from markupsafe import Markup
from urllib.parse import unquote
from werkzeug.datastructures import Headers

from odoo import models
from odoo.http import request, Response
from odoo.tools import date_utils
from ..jsonapi.utils import RESOURCE, RESOURCE_ID, RELATION, RESOURCE_ATTR

from odoo.addons.ekika_utils.tools.helpers import query_param_modifier
from odoo.addons.ekika_utils.tools.jsonapi_exceptions import ResourceNotFoundException

# https://api.example.com/<base>/<model.name>?
#     filter[title]=example&
#     include=author,comments&
#     sort=-created_at&
#     page[number]=1&
#     page[size]=10&
#     fields[articles]=title,body&
#     fields[users]=name,email&
#     fields[comments]=content


def validate_domain(domain):
    for domainItem in domain:
        if isinstance(domainItem, str):
            if domainItem not in ['&', '|']:
                raise 'filter error'
        elif hasattr(domainItem, '__iter__'):
            if len(domainItem) != 3:
                raise 'filter error'
        else:
            raise 'filter error'

class JsonAPIQuery():
    """Request parser to run query on Odoo ORM."""

    def __init__(self, request):
        """Initialize request."""
        self.request = request
        if request.easyapi.get('jsonapi_use_body_for_get'):
            self.params = json.loads(request.httprequest.get_data(as_text=True))
        else:
            self.params = self.request.params

        self._url = unquote(request.httprequest.url)
        self._apiurl = unquote(f'{request.httprequest.host_url}{request.base_endpoint}')
        self._resource = request.easyapi.get(RESOURCE)  # model in odoo
        self._sort = None  # order in odoo
        self._include = None  # relational fields on the model

        self.search_id = request.easyapi.get(RESOURCE_ID)
        self.model_field = request.easyapi.get(RESOURCE_ATTR)

        self.ids = []
        # /....?fields[resource]=<comma seperated fields withour quotes.>
        self.attributes = []
        self.filter = []
        self.domain = []
        self.fields = {}

        self.page = 1
        self.offset = 0
        self.length = 20

    @property
    def url(self):
        """Full request url."""
        return self._url

    @property
    def apiurl(self):
        """Base URL based on configuration in easy.api record.
        i.e. https://ekika.co/v1.1/
        'v1.1' is setup as endpoint in the easy.api record.
        """
        return self._apiurl

    @property
    def is_collection(self):
        """Returns true when request if collection call."""
        return not bool(self.search_id)

    @property
    def model(self):
        """Hopeful modals.Model."""
        return self._resource

    @property
    def include(self):
        """Relational field's demand."""
        return self._include

    @property
    def order(self):
        """Model's search Domain."""
        return self._sort

    def parse_fields(self):
        """
        Parse fields for Odoo from request.
        Here we are creating dictionary
        with key as model.name
        and value as list of fields.

        e.g: dict['sale.order'] = ['name','tag_ids', 'partner_id']
             dict['res.partner'] = ['name']
        """

        fields_dict = {}
        for key,val in self.params.items():
            if key.startswith('fields'):
                fields_dict[key[7:-1]] = val.split(',')
        self.fields = fields_dict
        # fields_param = self.request.get('fields', {})
        # if self.model in fields_param:
        #     self.fields = fields_param[self.model].split(',')

    def get_fields(self, model=None):
        """
        Return the list of fields for particular model
        """
        return self.fields.get(model or self.model)

    def parse_filter(self):
        domain = self.params.get('filter', '').replace('AND', '"&"').replace('OR', '"|"')
        if domain:
            domain = domain.replace("'",'"').replace('(','[').replace(')',']')
            domain = json.loads(domain)
            validate_domain(domain)
        self.filter = domain if domain else []

    # ToDo: Once refectoring done we can convert all using property.
    def get_filter(self):
        return self.filter

    def parse_pages(self):
        """Parse pagination for Odoo from request."""
        self.page = int(self.params.get('page[number]', '1'))
        length = self.params.get('page[size]', request.easyapi.get('pagesize'))
        self.length = int(length) if type(length) is str else length
        self.offset = max(0, self.page - 1) * self.length

    def get_page_info(self):
        return self.page, self.length, self.offset

    def get_model(self):
        guess_model = request.easyapi.get(RESOURCE)
        # If request is for relationship let's find model for it.
        if request.easyapi.get(RESOURCE_ATTR):
            pass

        if request.easyapi.get(RESOURCE):
            guess_model = request.easyapi.get(RESOURCE)

    def parse_request(self):
        """Parse the JSON:API request and query parameters."""
        # data = self.request.get('data', {})
        # self.model = data.get('type')
        # self.ids = [data.get('id')] if data.get('id') else []
        # self.attributes = data.get('attributes', [])

        # Parse fields
        self.parse_fields()

        # Parse include
        include = self.params.get('include')
        self._include = include.split(',') if include else None

        # Parse Sort
        sort = self.params.get('sort', '')
        self._sort = ','.join([
            f'{sitem[1:]} desc' if sitem.startswith('-') else f'{sitem}'
            for sitem in sort.split(',')
        ])


        # Parse filter
        self.parse_filter()

        # Parse pagination
        self.parse_pages()

class JsonAPIResponse(Response):
    """
    JSON:API Response based on v1.1 Spec.
    (spec: https://jsonapi.org/format/1.1/)
    """

    def __init__(self, *args, **kwargs):
        """
        {
            "data": [..., ...],
            "included": [..., ...],
            "links": {...},
            "errors": [..., ...],
            "meta": {...},
        }
        """
        self.jsonapi_data = kwargs.pop('data', [])
        self.jsonapi_included = kwargs.pop('included', [])
        self.jsonapi_links = kwargs.pop('links', {})
        self.jsonapi_errors = kwargs.pop('errors', [])
        meta = kwargs.pop('meta', {})
        self.jsonapi_meta = meta

        super().__init__(*args, **kwargs)

        # jsonapi's content-type never change.
        self.headers = Headers([('Content-Type', 'application/vnd.api+json')])

        # Hope request will be served successfully if there is error we have to process properly.
        # Use response_status to manage status
        self.status = '200'

    @property
    def response_status(self):
        return self.status

    @response_status.setter
    def response_status(self, value):
        if isinstance(value, int):
            value = str(value)
        self.status = value

    @property
    def is_api(self):
        return True

    def render(self):
        """Renders the Response's data, include and links and returns the result.

        Spec: https://jsonapi.org/format/1.1/#document-top-level

        MUST: data, errors, meta
        MAY: jsonapi, links, included

        The members data and errors MUST NOT coexist in the same document.
        """
        # Must have items.
        result = {"meta": self.jsonapi_meta}
        if self.jsonapi_errors:
            result["errors"] = self.jsonapi_errors
        else:
            result["data"] = self.jsonapi_data
        # May have items.
        may_items = ['included', 'links', 'jsonapi']
        result.update({
            k: getattr(self, f'jsonapi_{k}')
            for k in may_items if hasattr(self, f'jsonapi_{k}')
        })
        return Markup(json.dumps(result, ensure_ascii=False, default=date_utils.json_default))

    def flatten(self):
        """Forces the rendering of the response's template and sets the result
        as response body to serve."""
        self.response.append(self.render())


class EasyJsonApi(models.TransientModel):
    _name = 'easy.jsonapi'
    _description = "Json API Implementation"

    @classmethod
    def search_model(cls, query, model, search_id=None, domain=None):
        """
        Generates odoo model recordsets from standard odoo search() method
        considering various parameters such as model, domain, search_id, offset, limit, order
        """
        order = query.order
        page, limit, offset = query.get_page_info()
        if search_id:
            domain.append(('id', '=', search_id))

        try:
            main_model_data = request.env[model].search(domain, offset=offset,
                                                        limit=limit, order=order)
        except Exception as exc:
            raise exc
        else:
            return main_model_data

    @classmethod
    def search_model_data(cls, query):
        """
        Returns odoo model recordsets from url
        e.g:
            1. url: http://192.168.1.15:8017/jsonapi/sale.order?page[number]=3&page[size]=2
               returns: sale.order(12, 10)

            2. url: http://192.168.1.15:8017/jsonapi/sale.order/21/tag_ids?fields[crm.tag]=name
               returns: crm.tag(1, 3)

            3. http://192.168.1.15:8017/jsonapi/sale.order/21
               return: sale.order(21)
        """

        model_field = query.model_field
        search_id = query.search_id

        if model_field:
            # This case is considered when there is a relationships link.
            # e.g. url: http://192.168.1.15:8017/jsonapi/sale.order/21/tag_ids
            model_data = cls.search_model(query=query, model=query.model,
                                          search_id=search_id, domain=[])

            if len(model_data) == 0:
                raise ResourceNotFoundException(query.model, search_id)
            else:
                if request.httprequest.method == 'GET':
                    if model_data[model_field]:
                        second_model_ids = model_data[model_field].ids
                        model = model_data[model_field]._name
                        domain = query.get_filter()
                        if second_model_ids:
                            domain.append(('id', 'in', second_model_ids))
                        main_model_data = cls.search_model(query=query, model=model, domain=domain)

                    else:
                        main_model_data = model_data[model_field]

                    if len(main_model_data) == 0:
                        return main_model_data
                    else:
                        return main_model_data
                else:
                    main_model_data = model_data[model_field]
                    return main_model_data

        if search_id:
            # This case is considered when there is a normal link with a particular ID.
            # e.g. url: http://192.168.1.15:8017/jsonapi/sale.order/21
            main_model_data = cls.search_model(query=query, model=query.model,
                                               search_id=search_id, domain=[])
            if len(main_model_data) == 0:
                raise ResourceNotFoundException(query.model, search_id)
            else:
                return main_model_data

        # This case is considered when there is only a normal link.
        # e.g. url: http://192.168.1.15:8017/jsonapi/sale.order
        domain = query.get_filter()

        main_model_data = cls.search_model(query=query, model=query.model, domain=domain)
        return main_model_data

    @classmethod
    def generate_jsonapi_links(cls, query, count, pagesize, page):
        # links
        links = {'self': query.url}
        if query.is_collection and count > 1:
            lastpage = ceil(count / pagesize)
            query_params = {}
            query_params['page[number]'] = '1'
            links['first'] = query_param_modifier(query.url, query_params)
            query_params['page[number]'] =  str(max(1, page-1))
            links['prev'] = query_param_modifier(query.url, query_params)
            query_params['page[number]'] = str(min(lastpage, page+1))
            links['next'] = query_param_modifier(query.url, query_params)
            query_params['page[number]'] =   str(lastpage)
            links['last'] = query_param_modifier(query.url, query_params)
        return links

    @classmethod
    def serve_get(cls, query, response):
        """
        Main for GET
        """

        page, limit, offset = query.get_page_info()
        pagesize = limit

        # # data
        data_search = cls.search_model_data(query)
        count = data_search.search_count(query.get_filter())
        fields = query.get_fields(data_search._name)
        self_link = not bool(request.easyapi.get(RELATION))
        data = data_search.jsonapi_read(fields, query.apiurl, self_link=self_link)

        # include
        included = []
        include = query.include
        if include:
            included_by_type = {}
            simple, include_map = data_search.seperate_relational_fields(include)
            # First collect ids and than read to eliminate repetition
            for field, field_type in include_map.items():
                included_by_type.setdefault(field_type, []).extend(
                    getattr(data_search, field).ids
                )
            for include_model, ids in included_by_type.items():
                included.extend(
                    request.env[include_model].browse(ids).jsonapi_read(
                        query.get_fields(include_model), query.apiurl, relationships_links=False,
                    )
                )

        # links
        links = cls.generate_jsonapi_links(query, count, pagesize, page)

        response.jsonapi_data = data
        response.jsonapi_included =  included
        response.jsonapi_links = links
        return response

    @classmethod
    def generate_post_response(cls, model_data, data):
        data['data']['id'] = model_data.id
        data['data']['links'] = {
            'self': f"{request.httprequest.base_url}/{model_data.id}"
        }
        return data

    @classmethod
    def serve_post(cls, query, response):
        """
        Main For POST
        """
        data = json.loads(request.httprequest.get_data(as_text=True))
        model = query.model
        search_id = query.search_id
        model_field = query.model_field
        relationships = request.easyapi.get(RELATION)

        if model_field == 'execute':
            try:
                if search_id:
                    model_data = request.env[model].search([('id','=',search_id)])
                else:
                    model_data = request.env[model]
            except Exception as exc:
                raise exc
            if len(model_data) == 0:
                if search_id:
                    raise ResourceNotFoundException(model, search_id)
            try:
                method_name = data['data']['method']
                kwargs = data['data']['kwargs']
                method = getattr(model_data, method_name)
                values = method(**kwargs)
            except Exception as e:
                raise e

            data = {"result": "Success, request fulfilled"}
            try:
                if isinstance(values, models.BaseModel):
                    values = values.read(['id', values._rec_name])
                json.dumps(values, ensure_ascii=False, default=date_utils.json_default)
            except Exception as exc:
                data['value'] = 'Incompatible values'
            else:
                data['value'] = values
            response.jsonapi_data = data
            return response

        elif search_id and model_field and relationships:
            try:
                model_data = request.env[model].search([('id','=',search_id)])
            except Exception as exc:
                raise exc
            if len(model_data) == 0:
                raise ResourceNotFoundException(model, search_id)
            else:
                data = json.loads(request.httprequest.get_data(as_text=True))
                model_data.perform_write_operation(data=data, relationships=relationships,
                                                   model_field=model_field,
                                                   method=request.httprequest.method)
                response_data = cls.serve_get(query=query, response=response)
                return response_data

        else:
            new_model_data = request.env[model].perform_create_operation(data=data)
            data = cls.generate_post_response(new_model_data, data)
            response.headers['location'] = data['data']['links']['self']
            response.jsonapi_data = data['data']
            response.response_status = 201
            return response

    @classmethod
    def generate_patch_response(cls, data, relationships):
        if relationships:
            host_url = request.httprequest.host_url
            full_path = request.httprequest.full_path
            self_link = "".join([host_url[:-1], full_path])
            data['links'] = {'self': self_link}
            data['links'].update({'related': self_link.replace("/relationships", "" )})
            return data
        else:
            return data

    @classmethod
    def serve_patch(cls, query, response):
        """
        Main for PATCH
        """

        model = query.model
        search_id = query.search_id
        model_field = query.model_field
        relationships = request.easyapi.get(RELATION)

        if search_id and model_field and relationships:
            try:
                model_data = request.env[model].search([('id','=',search_id)])
            except Exception as exc:
                raise exc
            if len(model_data) == 0:
                raise ResourceNotFoundException(model, search_id)
            else:
                data = json.loads(request.httprequest.get_data(as_text=True))
                model_data.perform_write_operation(data=data, relationships=relationships,
                                                   model_field=model_field,
                                                   method=request.httprequest.method)
                response_data = cls.serve_get(query=query, response=response)
                return response_data

        elif search_id:
            try:
                model_data = request.env[model].search([('id','=',search_id)])
            except Exception as exc:
                raise exc
            if len(model_data) == 0:
                raise ResourceNotFoundException(model, search_id)
            else:
                data = json.loads(request.httprequest.get_data(as_text=True))
                model_data.perform_write_operation(data=data, relationships=relationships,
                                                   model_field=model_field,
                                                   method=request.httprequest.method)
                data = cls.generate_patch_response(data=data, relationships=relationships)
                response.jsonapi_data = data['data']
                return response

    @classmethod
    def serve_delete(cls, query, response):
        """
        Main for DELETE
        """
        model = query.model
        search_id = query.search_id
        model_field = query.model_field
        relationships = request.easyapi.get(RELATION)

        if search_id and model_field and relationships:
            try:
                model_data = request.env[model].search([('id','=',search_id)])
            except Exception as exc:
                raise exc
            if len(model_data) == 0:
                raise ResourceNotFoundException(model, search_id)
            else:
                data = json.loads(request.httprequest.get_data(as_text=True))
                model_data.perform_write_operation(data=data, relationships=relationships,
                                                   model_field=model_field,
                                                   method=request.httprequest.method)
                response_data = cls.serve_get(query=query, response=response)
                return response_data

        elif search_id:
            try:
                model_data = request.env[model].search([('id','=',search_id)])
            except Exception as exc:
                raise exc
            if len(model_data) == 0:
                raise ResourceNotFoundException(model, search_id)
            else:
                model_data.perform_delete_operation()
                return response

    @classmethod
    def serve(cls):
        #
        # {
        #     'fields[res.partner]': 'name,active,contract_ids',
        #     'include': 'contract_ids',
        #     'page[number]': '2',
        #     'page[size]': '5'
        # }
        query = JsonAPIQuery(request=request)
        query.parse_request()
        default_meta = {
            "version": "1.1",
            "author-info": {
                'author': request.easyapi['meta_author_name'],
                'author-email': request.easyapi['meta_author_email'],
            },
            "documentation-link": request.easyapi['meta_documentation_link'],
        }
        response = JsonAPIResponse(meta=default_meta)

        if request.httprequest.method == 'GET':
            return cls.serve_get(query, response)
        elif request.httprequest.method == 'POST':
            return cls.serve_post(query, response)
        elif request.httprequest.method == 'PATCH':
            return cls.serve_patch(query, response)
        elif request.httprequest.method == 'DELETE':
            return cls.serve_delete(query, response)
        else:
            raise 'Bad Query'

