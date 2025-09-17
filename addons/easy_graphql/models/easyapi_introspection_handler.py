# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields
from odoo.http import request
from odoo.addons.ekika_utils.tools.helpers import capitalize_to_odoo_model, convert_model_capitalize
from ..graphql_introspection_data import TYPES_DATA, DIRECTIVES_DATA, QUERY_MODEL_ARGS

# Initial Introspection Schema Defination
schema_map = {
    '__Type': {
        "name": "__Type",
        "fields": [
            { "name": "name" },
            { "name": "kind" },
            { "name": "description" },
            { "name": "fields" },
            { "name": "inputFields" },
            { "name": "interfaces" },
            { "name": "enumValues" },
            { "name": "possibleTypes" }
        ]
    },
    '__InputValue': {
        "name": "__InputValue",
        "fields": [
            { "name": "name" },
            { "name": "description" },
            { "name": "type" },
            { "name": "defaultValue" }
        ]
    },
    '__Directive': {
        "name": "__Directive",
        "fields": [
            { "name": "name" },
            { "name": "description" },
            { "name": "locations" },
            { "name": "args" },
            { "name": "isRepeatable" }
        ]
    },
    '__Schema': {
        "name": "__Schema",
        "fields": [
            { "name": "description" },
            { "name": "types" },
            { "name": "queryType" },
            { "name": "mutationType" },
            { "name": "subscriptionType" },
            { "name": "directives" }
        ]
    },
    "__Field": {
        "name": "__Field",
        "fields": [
            {
                "name": "name",
                "type": {
                    "name": "String"
                }
            },
            {
                "name": "description",
                "type": {
                    "name": "String"
                }
            },
            {
                "name": "args",
                "type": {
                    "name": "LIST"
                }
            },
            {
                "name": "type",
                "type": {
                    "name": None
                }
            },
            {
                "name": "isDeprecated",
                "type": {
                    "name": None
                }
            },
            {
                "name": "deprecationReason",
                "type": {
                    "name": "String"
                }
            }
        ]
    }
}


class EasyapiIntrospectionHandler(models.AbstractModel):
    _name = 'easyapi.introspection.handler'
    _description = "GraphQL Introspection Handler"

    @classmethod
    def get_model_fields_types(cls, data, model):
        """
        return model fields type,
        ToDo: currently default type is String
        """
        main_data = []
        model_data = request.env[model]
        for key in model_data._fields.keys():
            main_data.append({
                'name': key,
                'type': {'name': 'String'}
            })
        return main_data

    @classmethod
    def type_introspection_data(cls, data, variables, fragment_definitions):
        # ToDo
        model_name = [i['value']['value'] for i in data['arguments']
                      if i['name']['value']=='name'][0]
        odoo_model_name = capitalize_to_odoo_model(model_name)
        model_access_read = request.env['ir.model.access'].sudo().search(
            [('id','in',request.env.user.groups_id.model_access.ids),('perm_read','=',True)])
        accessible_models = [i.model for i in model_access_read.model_id]
        if odoo_model_name not in accessible_models:
            if model_name in schema_map:
                return schema_map[model_name]
            raise Exception(f'{model_name} not found!')
        main_data_dict = {}
        for selection in data['selection_set']['selections']:
            if selection['name']['value'] == 'name':
                main_data_dict['name'] = model_name
            elif selection['name']['value'] == 'kind':
                main_data_dict['kind'] = 'OBJECT'
            # get model fields types
            elif selection['name']['value'] == 'fields':
                main_data_dict['fields'] = cls.get_model_fields_types(selection, odoo_model_name)
        return main_data_dict

    @classmethod
    def fetch_accessible_model(cls):
        """
        Return models dictionary which are accessible by requested user
        ToDo: currently fetch models which has "read" permission

        ToDo: remarks: 
                we are not fetching models which are starts with "base"
                also rejetcted model = ['_unknown']
                we are not fetching models which are abstract and transient

        returns --> {
                    'sale.order': sale.order()
                }
        """
        model_access_read = request.env['ir.model.access'].sudo().search(
            [('id','in',request.env.user.groups_id.model_access.ids), ('perm_read','=',True)])
        accessible_models_name = [i.model for i in model_access_read.model_id
                                  if not i.model.startswith('base')]
        all_models_obj = dict(request.env.items())
        reject_model = ['_unknown']
        accessible_models = {
            val:all_models_obj[val] for val in accessible_models_name if
            (not val.startswith('base') and not all_models_obj[val]._abstract and
             not all_models_obj[val]._transient and val not in reject_model)
            }
        return accessible_models

    @classmethod
    def query_model_data(cls, accessible_models):
        main_data = []
        for model, model_obj in accessible_models.items():
            model_name = convert_model_capitalize(model)
            main_dict = {
                'name': model_name,
                'description': model_obj._description,
                'args': QUERY_MODEL_ARGS,
                "type": {
                    "kind": "OBJECT",
                    "name": model_name,
                    "ofType": None
                },
                "isDeprecated": False,
                "deprecationReason": None
            }
            main_data.append(main_dict)

        # For Export Data
        export_dict = {
            'name': 'ExportData',
            'description': model_obj._description,
            'args': [
                {
                "name": "ExportValues",
                "description": None,
                "type": {
                    "kind": "SCALAR",
                    "name": "Any",
                    "ofType": None
                    },
                "defaultValue": None
                },
            ],
            "type": {
                "kind": "OBJECT",
                "name": 'ExportData',
                "ofType": None
            },
            "isDeprecated": False,
            "deprecationReason": None
        }

        # For Report Data
        report_dict = {
            'name': 'ReportData',
            'description': model_obj._description,
            'args': [
                {
                    "name": "converter",
                    "description": None,
                    "type": {
                        "kind": "SCALAR",
                        "name": "String",
                        "ofType": None
                    },
                    "defaultValue": None
                },
                {
                    "name": "report_ref",
                    "description": None,
                    "type": {
                        "kind": "SCALAR",
                        "name": "String",
                        "ofType": None
                    },
                    "defaultValue": None
                },
                {
                    "name": "res_ids",
                    "description": None,
                    "type": {
                        'kind': 'LIST',
                        'name':None,
                        "ofType": {
                            "kind": "SCALAR",
                            "name": "Int",
                            "ofType": None
                        }
                    },
                    "defaultValue": None
                },
                {
                    "name": "data",
                    "description": None,
                    "type": {
                        "kind": "SCALAR",
                        "name": "Any",
                        "ofType": None
                    },
                    "defaultValue": None
                },
            ],
            "type": {
                "kind": "OBJECT",
                "name": 'ReportData',
                "ofType": None
            },
            "isDeprecated": False,
            "deprecationReason": None
        }
        main_data.append(export_dict)
        main_data.append(report_dict)
        return main_data

    @classmethod
    def make_mutation_models_args(cls, model):
        return [
            {
                'name': 'id',
                'description': None,
                'type': {
                    'kind': 'SCALAR',
                    'name': 'ID',
                    'ofType': None,
                },
                'defaultValue': None
            },
            {
                'name': f'{convert_model_capitalize(model)}Values',
                "type": {
                    "kind": "INPUT_OBJECT",
                    "name": f'{convert_model_capitalize(model)}Values',
                    "ofType": None
                }
            },
            {
                'name': 'method_name',
                'description': "name of the model method you want to execute.",
                'type': {
                    'kind': 'SCALAR',
                    'name': 'Any',
                    'ofType': None,
                },
                'defaultValue': None
            },
            {
                'name': 'method_parameters',
                'description': "paramters of the method.",
                'type': {
                    'kind': 'SCALAR',
                    'name': 'Any',
                    'ofType': None,
                },
                'defaultValue': None
            }
        ]

    @classmethod
    def mutation_model_data(cls, accessible_models):
        main_data = []
        for model, model_obj in accessible_models.items():
            model_name = convert_model_capitalize(model)
            main_dict = {
                'name': model_name,
                'description': model_obj._description,
                'args': cls.make_mutation_models_args(model),
                "type": {
                    "kind": "OBJECT",
                    "name": model_name,
                    "ofType": None
                },
                "isDeprecated": False,
                "deprecationReason": None
            }
            main_data.append(main_dict)
        return main_data

    @classmethod
    def make_query_type_data(cls, accessible_models):
        main_data_dict = {
            'kind': 'OBJECT',
            'name': 'Root',
            'description': None,
            'fields': cls.query_model_data(accessible_models),
            'inputFields': None,
            "interfaces": [],
            "enumValues": None,
            "possibleTypes": None
        }
        return main_data_dict

    @classmethod
    def make_mutation_type_data(cls, accessible_models):
        main_data_dict = {
            'kind': 'OBJECT',
            'name': 'EasyMutation',
            'description': None,
            'fields': cls.mutation_model_data(accessible_models),
            'inputFields': None,
            "interfaces": [],
            "enumValues": None,
            "possibleTypes": None
        }
        return main_data_dict

    @classmethod
    def get_field_type_data(cls, field):
        if field.type in ['many2one', 'many2many', 'one2many']:
            data_dict = {
                'kind': 'OBJECT',
                'name': convert_model_capitalize(field.comodel_name),
                'ofType': None
            }
            return data_dict
        elif field.type == 'boolean':
            data_dict = {
                'kind': 'SCALAR',
                'name': 'Boolean',
                'ofType': None
            }
            return data_dict
        elif field.type == 'integer':
            data_dict = {
                'kind': 'SCALAR',
                'name': 'Int',
                'ofType': None
            }
            return data_dict
        elif field.type == 'float':
            data_dict = {
                'kind': 'SCALAR',
                'name': 'Float',
                'ofType': None
            }
            return data_dict
        else:
            data_dict = {
                'kind': 'SCALAR',
                'name': 'String',
                'ofType': None
            }
            return data_dict

    @classmethod
    def generate_model_fields_data(cls, model_obj):
        main_data = []

        model_fields = model_obj._fields
        if model_fields:
            # remove fields that starts with "__" because it is reserved by GraphQL introspection.
            field_items ={key:val for key,val in model_fields.items() if not key.startswith('__')}
            for key,val in field_items.items():
                main_dict = {
                    'name': key,
                    'description': val.string,
                    'args': [],
                    'type': cls.get_field_type_data(val),
                    'isDeprecated': False,
                    'deprecationReason': None
                }
                main_data.append(main_dict)
        else:
            # ToDo: If model does not have fields,
            # then we are passing default fields, because it is compulsary to have field
            # in graphql-introspection to generate schema and documentation 
            main_dict = {
                'name': 'No_Fields',
                'description': f'{convert_model_capitalize(model_obj._name)} does not have field',
                'args': [],
                'type': {
                    'kind': 'SCALAR',
                    'name': 'String',
                    'ofType': None
                    },
                'isDeprecated': False,
                'deprecationReason': None
            }
            main_data.append(main_dict)
        return main_data

    @classmethod
    def fetch_co_models(cls, accessible_models):
        co_models = set()
        model_name_list = list(accessible_models.keys())
        for model, model_obj in accessible_models.items():
            for field in model_obj._fields:
                field_obj = model_obj._fields[field]
                if isinstance(field_obj, (fields.Many2one, fields.One2many, fields.Many2many)):
                    related_model_name = field_obj.comodel_name
                    if related_model_name:
                        if related_model_name not in model_name_list:
                            co_models.add(related_model_name)
        return [request.env[val] for val in co_models]

    @classmethod
    def get_co_models_data(cls, accessible_models):
        main_data = []
        co_models = cls.fetch_co_models(accessible_models)
        for val in co_models:
            main_dict = {
                'kind': 'OBJECT',
                'name': convert_model_capitalize(val._name),
                'description': val._description,
                # ToDO: Currenlty we are fetching only id field for co-model
                'fields': [{
                    'name': 'id',
                    'description': 'ID',
                    'args': [],
                    'type': {
                        'kind': 'SCALAR',
                        'name': 'String',
                        'ofType': None
                    },
                    'isDeprecated': False,
                    'deprecationReason': None
                }],
                'inputFields': None,
                'interfaces': [],
                'enumValues': None,
                'possibleTypes': None
            }
            main_data.append(main_dict)
        return main_data

    @classmethod
    def make_model_type_data(cls, accessible_models):
        main_data = []
        for model, model_obj in accessible_models.items():
            main_dict = {
                'kind': 'OBJECT',
                'name': convert_model_capitalize(model),
                'description': model_obj._description,
                'fields': cls.generate_model_fields_data(model_obj),
                'inputFields': None,
                'interfaces': [],
                'enumValues': None,
                'possibleTypes': None
            }
            main_data.append(main_dict)

        # Fetch model data which are not in accessbile models,
        # but, co-model which are part of accessible_models relational fields
        comodels_data = cls.get_co_models_data(accessible_models)
        main_data.extend(comodels_data)
        return main_data
    
    @classmethod
    def export_type_data(cls):
        return {
                'kind': 'OBJECT',
                'name': 'ExportData',
                'description': 'For export data',
                'fields': [
                    {
                        'name': 'No_Fields',
                        'description': 'There is not any fields for export-data',
                        'args': [],
                        'type': {
                            'kind': 'SCALAR',
                            'name': 'Any',
                            'ofType': None
                            },
                        'isDeprecated': False,
                        'deprecationReason': None
                    }
                ],
                'inputFields': None,
                'interfaces': [],
                'enumValues': None,
                'possibleTypes': None
        }

    @classmethod
    def report_type_data(cls):
        return {
            'kind': 'OBJECT',
            'name': 'ReportData',
            'description': 'For Report Data',
            'fields': [
                {
                    'name': 'No_Fields',
                    'description': 'There is not any fields for export-data',
                    'args': [],
                    'type': {
                        'kind': 'SCALAR',
                        'name': 'Any',
                        'ofType': None
                        },
                    'isDeprecated': False,
                    'deprecationReason': None
                }
            ],
            'inputFields': None,
            'interfaces': [],
            'enumValues': None,
            'possibleTypes': None
        }

    @classmethod
    def get_input_field_type_data(cls, field):
        if field.type in ['many2one', 'many2many', 'one2many']:
            data_dict = {
                'kind': 'SCALAR',
                'name': f'Any',
                'ofType': None
            }
            return data_dict
        elif field.type == 'boolean':
            data_dict = {
                'kind': 'SCALAR',
                'name': 'Boolean',
                'ofType': None
            }
            return data_dict
        elif field.type == 'integer':
            data_dict = {
                'kind': 'SCALAR',
                'name': 'Int',
                'ofType': None
            }
            return data_dict
        elif field.type == 'float':
            data_dict = {
                'kind': 'SCALAR',
                'name': 'Float',
                'ofType': None
            }
            return data_dict
        else:
            data_dict = {
                'kind': 'SCALAR',
                'name': 'String',
                'ofType': None
            }
            return data_dict

    @classmethod
    def make_model_input_fields(cls, model_obj):
        main_data = []
        if model_obj._fields:
            field_items ={key:val for key,val in model_obj._fields.items()
                            if not key.startswith('__')}
            for key, val in field_items.items():
                data_dict = {
                    'name': key,
                    'description': val.string,
                    'type': cls.get_input_field_type_data(val),
                    'defaultValue': None,
                }
                main_data.append(data_dict)
        else:
            data_dict = {
                'name': "NoFields",
                'description': f'There is not any fields for {model_obj._name}',
                'type': {
                    'kind': 'SCALAR',
                    'name': 'String',
                    'ofType': None
                },
                'defaultValue': None,
            }
            main_data.append(data_dict)
        return main_data

    @classmethod
    def make_input_object_type_data(cls, accessible_models):
        main_data = []
        for model, model_obj in accessible_models.items():
            main_dict = {
                'kind': 'INPUT_OBJECT',
                'name': f'{convert_model_capitalize(model)}Values',
                'description': f'Fields for {model}',
                'fields': None,
                'inputFields': cls.make_model_input_fields(model_obj),
                'interfaces': [],
                'enumValues': None,
                'possibleTypes': None,
            }
            main_data.append(main_dict)
        return main_data

    @classmethod
    def schema_types_data(cls):
        types_data = []
        accessible_models = cls.fetch_accessible_model()
        query_type_data = cls.make_query_type_data(accessible_models)
        types_data.append(query_type_data)
        mutation_type_data = cls.make_mutation_type_data(accessible_models)
        types_data.append(mutation_type_data)
        types_data.extend(TYPES_DATA)
        input_object_type_data = cls.make_input_object_type_data(accessible_models)
        types_data.extend(input_object_type_data) 
        model_type_data = cls.make_model_type_data(accessible_models)
        types_data.extend(model_type_data)
        types_data.append(cls.export_type_data())
        types_data.append(cls.report_type_data())
        return types_data

    @classmethod
    def schema_directives(cls):
        directives_data = DIRECTIVES_DATA
        return directives_data

    @classmethod
    def schema_mutation_type_data(cls):
        return None

    @classmethod
    def schema_subscription_type_data(cls):
        return None

    @classmethod
    def schema_introspection_data(cls, data, variables, fragment_definitions):
        main_data_dict = {}
        for selection in data['selection_set']['selections']:
            if selection['name']['value'] == 'queryType':
                main_data_dict['queryType'] = {"name": "Root"}
            elif selection['name']['value'] == 'types':
                main_data_dict['types'] = cls.schema_types_data()
            elif selection['name']['value'] == 'mutationType':
                main_data_dict['mutationType'] ={"name": "EasyMutation"}
            elif selection['name']['value'] == 'subscriptionType':
                main_data_dict['subscriptionType'] = cls.schema_subscription_type_data()
            elif selection['name']['value'] == 'directives':
                main_data_dict['directives'] = cls.schema_directives()
        return main_data_dict

    @classmethod
    def query_introspection(cls, data, variables, fragment_definition):
        main_data_dict = {}
        if data['name']['value'] == '__schema':
            main_data_dict = cls.schema_introspection_data(data, variables, fragment_definition)
            return main_data_dict
        elif data['name']['value'] == '__type':
            main_data_dict = cls.type_introspection_data(data, variables, fragment_definition)
            return main_data_dict

