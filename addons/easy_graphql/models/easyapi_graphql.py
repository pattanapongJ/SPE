# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

import json
from base64 import b64encode
# pip install graphql-core==3.1.5
from graphql import parse
from graphql.language import Node, OperationType
from typing import (
    Any,
    ByteString,
    Collection,
    Iterable,
    Mapping,
    Text,
    ValuesView,
)
from typing import Any, Collection, Dict, List, Optional, overload
from werkzeug.exceptions import NotFound
from odoo import models
from odoo.http import request
from odoo.tools import date_utils
from odoo.addons.ekika_utils.tools.helpers import capitalize_to_odoo_model


class EasyapiGraphql(models.AbstractModel):
    _name = 'easyapi.graphql'
    _description = "GraphQL Methods"


    @classmethod
    def check_is_node_iterable(cls, value):
        return isinstance(value, Iterable) and not isinstance(
            value, (ByteString, Mapping, Text)
        )

    @classmethod
    def parse_query_to_dict(cls, node, locations=False, cache=None):
        if isinstance(node, Node):
            if cache is None:
                cache = {}
            elif node in cache:
                return cache[node]
            cache[node] = res = {}
            res.update({
                    key: cls.parse_query_to_dict(getattr(node, key), locations, cache)
                    for key in ("kind",) + tuple(node.keys[1:])
                })
            if locations:
                loc = node.loc
                if loc:
                    res["loc"] = dict(start=loc.start, end=loc.end)
            return res
        if cls.check_is_node_iterable(node):
            return [cls.parse_query_to_dict(sub_node, locations, cache) for sub_node in node]
        if isinstance(node, OperationType):
            return node.value
        return node

    @classmethod
    def parse_query(cls, query):
        """
        Returns parsed query as dictionary
        """
        parsed_query = parse(query)
        return cls.parse_query_to_dict(parsed_query)

    @classmethod
    def convert_list_value(cls, values):
        if values['kind'] == 'list_value':
            return [cls.convert_list_value(val) for val in values['values']]
        else:
            return values['value']

    @classmethod
    def convert_object_value(cls, values, variables):
        return {val['name']['value']: cls.parse_argument_value(val['value'], variables)
                for val in values['fields']}

    @classmethod
    def parse_pages(cls, limit=None, offset=None):
        """Parse pagination using offset, limits for Odoo"""
        length = limit if limit else request.easyapi.get('pagesize')
        limit = int(length) if type(length) is str else length
        offset = int(offset) if type(offset) is str else offset
        return limit, offset

    @classmethod
    def parse_argument_value(cls, value, variables):
        # when argument is variable
        if value['kind'] == 'variable':
            return variables.get(value['name']['value'])
        # when argument is list values
        elif value['kind'] == 'list_value':
            return cls.convert_list_value(value)
        # when argument is object-values(dictionary)
        elif value['kind'] == 'object_value':
            return cls.convert_object_value(value, variables)
        # when argument is normal value like String, Boolean, Int etc.
        else:
            return value.get('value', None)

    @classmethod
    def parse_arguments(cls, arguments, variables):
        values = {val['name']['value']:val['value'] for val in arguments}
        parse_values = {key:cls.parse_argument_value(val, variables) for key,val in values.items()}
        return parse_values

    @classmethod
    def parse_selections(cls, data, variables, fragment_definitions):
        fields_list = []
        for selection in data:
            if selection['kind'] == 'field':
                if cls.parse_directives(data=selection, variables=variables):
                    # If there is nested fields
                    if selection.get('selection_set'):
                        nested_values = cls.parse_selections(
                            data=selection['selection_set']['selections'], variables=variables,
                            fragment_definitions=fragment_definitions)
                        alias = selection['alias']
                        fields_list.append(
                            {
                                selection['name']['value']:{
                                    'nested_fields': nested_values,
                                    'alias': alias['value'] if alias else None
                                    }
                                }
                            )
                    else:
                        alias = selection['alias']
                        fields_list.append(
                            {
                                selection['name']['value']:{
                                    'nested_fields': None,
                                    'alias': alias['value'] if alias else None
                                    }
                                }
                            )
            elif selection['kind'] == 'fragment_spread':
                if cls.parse_directives(data=selection, variables=variables):
                    fields = cls.parse_fragments(data=selection, variables=variables,
                                                 fragment_definitions=fragment_definitions)
                    fields_list.extend(fields)
            elif selection['kind'] == 'inline_fragment':
                if cls.parse_directives(data=selection, variables=variables):
                    if selection.get('selection_set'):
                        fields = cls.parse_selections(
                            data=selection['selection_set']['selections'], variables=variables,
                            fragment_definitions=fragment_definitions)
                        fields_list.extend(fields)
        return fields_list

    @classmethod
    def parse_fragments(cls, data, variables, fragment_definitions):
        fragment_definition = [v for v in fragment_definitions
                               if v['name']['value']==data['name']['value']][0]
        if cls.parse_directives(data=fragment_definition, variables=variables):
            if fragment_definition.get('selection_set'):
                return cls.parse_selections(data=fragment_definition['selection_set']['selections'],
                                            variables=variables,
                                            fragment_definitions=fragment_definitions)
        else:
            return []

    @classmethod
    def parse_directives(cls, data, variables):
        if data['directives']:
            if data['directives'][0]['name']['value'] == 'include':
                variable = data['directives'][0]['arguments'][0]['value']['name']['value']
                return variables[variable]
            elif data['directives'][0]['name']['value'] == 'skip':
                variable = data['directives'][0]['arguments'][0]['value']['name']['value']
                return not variables[variable]
        else:
            return True

    @classmethod
    def parse_fields(cls, data, variables, fragment_definitions):
        if data.get('selection_set'):
            return cls.parse_selections(data=data['selection_set']['selections'],
                                        variables=variables,
                                        fragment_definitions=fragment_definitions)
        else:
            return []

    @classmethod
    def graphql_many_to_one_read(cls, model, fields):
        if not model:
            return None
        data_dict = {}
        for field in fields:
            main_key = [v for v in field][0]
            alias = field[main_key]['alias']
            nested_fields = field[main_key]['nested_fields']
            display_key = alias if alias else main_key
            if nested_fields:
                if model._fields[main_key].type == 'many2one':
                    data_dict[display_key] = cls.graphql_many_to_one_read(model=model[main_key],
                                                                        fields=nested_fields)
                elif model._fields[main_key].type in ['one2many','many2many']:
                    data_dict[display_key] = cls.graphql_read(models=model[main_key],
                                                            fields=nested_fields)
            else:
                if model._fields[main_key].type == 'many2one':
                    if model[main_key]:
                        data_dict[display_key] = model[main_key].id
                    else:
                        data_dict[display_key] = None
                elif model._fields[main_key].type in ['one2many','many2many']:
                    data_dict[display_key] = model[main_key].ids
                else:
                    data_dict[display_key] = model[main_key]
        return data_dict

    @classmethod
    def graphql_read(cls, models, fields):
        main_data = []
        for model in models:
            data_dict = {}
            for field in fields:
                main_key = [v for v in field][0]
                alias = field[main_key]['alias']
                nested_fields = field[main_key]['nested_fields']
                display_key = alias if alias else main_key
                if nested_fields:
                    if model._fields[main_key].type == 'many2one':
                        data_dict[display_key] = cls.graphql_many_to_one_read(model=model[main_key],
                                                                            fields=nested_fields)
                    elif model._fields[main_key].type in ['one2many','many2many']:
                        data_dict[display_key] = cls.graphql_read(models=model[main_key],
                                                                fields=nested_fields)
                else:
                    if model._fields[main_key].type == 'many2one':
                        if model[main_key]:
                            data_dict[display_key] = model[main_key].id
                        else:
                            data_dict[display_key] = None
                    elif model._fields[main_key].type in ['one2many','many2many']:
                        data_dict[display_key] = model[main_key].ids
                    else:
                        data_dict[display_key] = model[main_key]
            main_data.append(data_dict)
        return main_data

    @classmethod
    def handle_graphql_report(cls, arguments, variables):
        values = cls.parse_arguments(arguments, variables)
        if not values.get('converter') and not values.get('report_ref'):
            raise Exception('Provide inputs')
        try:
            converter = values.get('converter')
            report_ref = values.get('report_ref')
            res_ids = values.get('res_ids')
            res_ids = [int(res_id) for res_id in res_ids]
            data = values.get('data')
            ir_report = request.env['ir.actions.report']._get_report_from_name(report_ref)
            if converter == 'html':
                html = ir_report._render_qweb_html(res_ids, data=data)[0]
                result_data = {"file_data": f"{b64encode(html).decode()}"}
                return result_data
            elif converter == 'pdf':
                pdf = ir_report._render_qweb_pdf(res_ids, data=data)[0]
                result_data = {"file_data": f"{b64encode(pdf).decode()}"}
                return result_data
            elif converter == 'text':
                text = ir_report._render_qweb_text(res_ids, data=data)[0]
                result_data = {"file_data": f"{b64encode(text).decode()}"}
                return result_data
            else:
                raise Exception('Provide valid converter')
        except Exception as exc:
            raise exc

    @classmethod
    def query_operation(cls, data, variables, fragment_definitions):
        """
        Query operation is used for read data from the server.
        """
        main_data_dict = {}
        data_dict = {}
        page_info_dict = {}
        for selection in data['selection_set']['selections']:
            # For introspection query
            if selection['name']['value'] in ['__schema', '__type']:
                introspection_handler = request.env['easyapi.introspection.handler']
                key = selection['name']['value']
                data_dict[key] = introspection_handler.query_introspection(selection, variables,
                                                                           fragment_definitions)
            # For Export Data Query query
            elif selection['name']['value'] == 'ExportData':
                export_handler = request.env['easyapi.graphql.export']
                export_result = export_handler.handle_graphql_export(selection, variables)
                return export_result
            elif selection['name']['value'] == 'ReportData':
                report_result = cls.handle_graphql_report(selection['arguments'], variables)
                return report_result
            # For Read Query
            else:
                if cls.parse_directives(data=selection, variables=variables):
                    model_name = capitalize_to_odoo_model(model=selection['name']['value'])
                    arguments = selection['arguments']
                    values = cls.parse_arguments(arguments, variables)
                    limit, offset = cls.parse_pages(values.get('limit'), values.get('offset',0))
                    order = values.get('order')
                    domain = values.get('domain') or []
                    search_id = values.get('id')
                    if search_id:
                        domain = [("id","=", int(search_id))]
                    main_model = request.env[model_name].search(args=domain, offset=offset,
                                                                limit=limit, order=order)

                    # Parsing Fields
                    main_fields = cls.parse_fields(data=selection, variables=variables,
                                                   fragment_definitions=fragment_definitions)
                    main_data = cls.graphql_read(models=main_model, fields=main_fields)
                    alias = selection['alias']
                    display_key = alias['value'] if alias else selection['name']['value']
                    data_dict[display_key] = main_data

                    #Add Page Inforamtion
                    count = main_model.search_count(domain)
                    has_next = bool((offset+limit) < count)
                    page_info_dict[display_key] = {
                        'totalCount': count,
                        'hasNextPage': has_next
                    }

        data_dict['pageInfo'] = page_info_dict
        main_data_dict['data'] = data_dict
        return main_data_dict

    @classmethod
    def parse_object_value(cls, data, variables, fragment_definitions):
        data_dict = {}
        for v in data:
            value =  cls.parse_fields_values(data=v['value'],
                                             variables=variables,
                                             fragment_definitions=fragment_definitions)
            data_dict[f'{v["name"]["value"]}'] = value
        return data_dict

    @classmethod
    def parse_fields_values(cls, data, variables, fragment_definitions):
        if data['kind'] == 'list_value':
            values = [
                cls.parse_fields_values(data=val,
                                        variables=variables,
                                        fragment_definitions=fragment_definitions)
                    for val in data['values']
                ]
            return values
        elif data['kind'] == 'object_value':
            values = cls.parse_object_value(data=data['fields'],
                                            variables=variables,
                                            fragment_definitions=fragment_definitions)
            return values
        elif data['kind'] == 'variable':
            return cls.parse_argument_value(data, variables)
        else:
            value = data.get('value')
            if isinstance(value, str) and value.isdigit():
                return int(value)
            else:
                return value

    @classmethod
    def parse_values_arguments(cls, data, variables, fragment_definitions, param):
        argument = [val for val in data if val['name']['value'] == param][0]
        argument_fields = argument['value']['fields']
        main_dict = {}
        for field in argument_fields:
            fields_value = cls.parse_fields_values(data=field['value'],
                                                   variables=variables,
                                                   fragment_definitions=fragment_definitions)
            main_dict[f'{field["name"]["value"]}'] = fields_value
        return main_dict

    @classmethod
    def create_operation(cls, data, variables, fragment_definitions):
        main_data_dict = {}
        data_dict = {}
        for selection in data:
            if cls.parse_directives(data=selection, variables=variables):
                model_name = capitalize_to_odoo_model(model=selection['name']['value'])
                model = request.env[model_name]
                fields_values = cls.parse_values_arguments(
                    data=selection['arguments'],
                    variables=variables,
                    fragment_definitions=fragment_definitions,
                    param=f'{selection["name"]["value"]}Values')
                new_record = model.create(fields_values)
                main_fields = cls.parse_fields(data=selection,
                                               variables=variables,
                                               fragment_definitions=fragment_definitions)
                main_data = cls.graphql_read(models=new_record, fields=main_fields)
                alias = selection['alias']
                display_key = alias['value'] if alias else selection['name']['value']
                data_dict[display_key] = main_data

        main_data_dict['data'] = data_dict
        return main_data_dict

    @classmethod
    def update_operation(cls, data, variables, fragment_definitions):
        main_data_dict = {}
        data_dict = {}
        for selection in data:
            if cls.parse_directives(data=selection, variables=variables):
                model_name = capitalize_to_odoo_model(model=selection['name']['value'])
                values = cls.parse_arguments(selection['arguments'], variables)
                search_id = values.get('id')
                model = request.env[model_name].search([('id','=',search_id)])
                if not model:
                    raise NotFound(f'id: {search_id} Not Found')
                fields_values = cls.parse_values_arguments(
                    data=selection['arguments'],
                    variables=variables,
                    fragment_definitions=fragment_definitions,
                    param=f'{selection["name"]["value"]}Values')
                model.write(fields_values)
                main_fields = cls.parse_fields(data=selection,
                                               variables=variables,
                                               fragment_definitions=fragment_definitions)
                main_data = cls.graphql_read(models=model, fields=main_fields)
                alias = selection['alias']
                display_key = alias['value'] if alias else selection['name']['value']
                data_dict[display_key] = main_data

        main_data_dict['data'] = data_dict
        return main_data_dict

    @classmethod
    def delete_operation(cls, data, variables, fragment_definitions):
        main_data_dict = {}
        data_dict = {}
        for selection in data:
            if cls.parse_directives(data=selection, variables=variables):
                model_name = capitalize_to_odoo_model(model=selection['name']['value'])
                values = cls.parse_arguments(selection['arguments'], variables)
                search_id = values.get('id')
                model = request.env[model_name].search([('id','=',search_id)])
                if not model:
                    raise NotFound(f'id: {search_id} Not Found')
                model.unlink()
                data_dict['delete'] = 'Success'
        main_data_dict['data'] = data_dict
        return main_data_dict

    @classmethod
    def parse_method_parameters(cls, values, variables):
        if values['kind'] == 'object_value':
            method_parameters = cls.convert_object_value(values, variables)
            return method_parameters
        elif values['kind'] == 'variable':
            variable_value = variables.get(values['name']['value'])
            return variable_value if variable_value else {}
        elif values['kind'] == 'null_value':
            return {}

    @classmethod
    def method_execute(cls, data, variables, fragment_definitions):
        main_data_dict = {}
        data_dict = {}
        for selection in data:
            if cls.parse_directives(data=selection, variables=variables):
                model_name = capitalize_to_odoo_model(model=selection['name']['value'])
                values = cls.parse_arguments(selection['arguments'], variables)
                model = request.env[model_name]
                search_id = values.get('id')
                if search_id and isinstance(search_id, list):
                    search_domain = [('id', 'in', search_id)]
                    model = request.env[model_name].search(search_domain)
                elif search_id and isinstance(search_id, (str, int)):
                    search_domain = [('id', '=', search_id)]
                    model = request.env[model_name].search(search_domain)
                method_name = values.get('method_name')
                method_parameters = values.get('method_parameters')
                method = getattr(model, method_name)
                result = method(**method_parameters)
                data_dict['method'] = f'Success, {method_name} executed'
                try:
                    if isinstance(result, models.BaseModel):
                        result = result.read(['id', result._rec_name])
                    json.dumps(result, ensure_ascii=False, default=date_utils.json_default)
                except Exception as exc:
                    data_dict['result'] = 'Incompatible result'
                else:
                    data_dict['result'] = result
        main_data_dict['data'] = data_dict
        return main_data_dict

    @classmethod
    def mutation_operation(cls, data, variables, fragment_definitions):
        """
        Mutation operation is used for modify data on the server. like create, update, delete.
        """
        if cls.parse_directives(data=data, variables=variables):
            operation_type = data['name']['value']
            if operation_type == 'Create':
                data = cls.create_operation(data=data['selection_set']['selections'],
                                            variables=variables,
                                            fragment_definitions=fragment_definitions)
                return data
            elif operation_type == 'Update':
                data = cls.update_operation(data=data['selection_set']['selections'],
                                            variables=variables,
                                            fragment_definitions=fragment_definitions)
                return data
            elif operation_type == 'Delete':
                data = cls.delete_operation(data=data['selection_set']['selections'],
                                            variables=variables,
                                            fragment_definitions=fragment_definitions)
                return data
            elif operation_type == 'Method':
                data = cls.method_execute(data=data['selection_set']['selections'],
                                            variables=variables,
                                            fragment_definitions=fragment_definitions)
                return data

    @classmethod
    def handle_query(cls, data):
        data = json.loads(data)
        query_dict = cls.parse_query(query=data['query'])
        variables = data.get('variables')

        operation_definitions = [rec for rec in query_dict['definitions']
                                if rec['kind']=='operation_definition']
        fragment_definitions = [rec for rec in query_dict['definitions']
                                if rec['kind']=='fragment_definition']

        for val in operation_definitions:
        #check if operation_type if it is query or mutation
            if val['operation'] == 'query':
                data = cls.query_operation(val, variables, fragment_definitions)
                return data
            if val['operation'] == 'mutation':
                data = cls.mutation_operation(val, variables, fragment_definitions)
                return data

