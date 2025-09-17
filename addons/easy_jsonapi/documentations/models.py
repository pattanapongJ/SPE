# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models

class Base(models.AbstractModel):
    _inherit = 'base'

    def generate_openapi_components_schemas(self):
        unrelational_fields = [key for key,val in self._fields.items() if val.type not in ['many2one','one2many','many2many']]
        components_schemas_dict = {f'{self._name}_attributes_schema': {'type': 'object', 'title': f'{self._name} schema', 'properties': {}}}
        components_schemas_dict.update({f'{self._name}': {
                'properties': {
                    'type': {'type': 'string', 'example': self._name},
                    'id': {'type': 'integer', 'example': 123},
                    'attributes': {'type': 'object', '$ref': f'#/components/schemas/{self._name}_attributes_schema'},
                    'relationships': {'type': 'object', '$ref': f'#/components/schemas/{self._name}_relationships_schema'}
                },
                'required': ['type', 'id', 'attributes', 'relationships']
                }
            })
        for f in unrelational_fields:
            components_schemas_dict[f'{self._name}_attributes_schema']['properties'][f] = self._fields[f].get_schema_properties(record=self)
        relational_fields = [key for key,val in self._fields.items() if val.type in ['many2one','one2many','many2many']]
        components_schemas_dict[f'{self._name}_relationships_schema'] = {'type': 'object','title': f'{self._name} schemas', 'properties': {}}
        for f in relational_fields:
            components_schemas_dict[f'{self._name}_relationships_schema']['properties'][f] = self._fields[f].get_schema_properties(record=self)
            components_schemas_dict[f'relationships_{f}_data'] = {'properties': {}, 'required': ['links']}
            components_schemas_dict[f'relationships_{f}_data']['properties'] = self._fields[f].get_relationships_field_data(record=self)
            components_schemas_dict[f'{f}_data_field'] = {'properties': {}, 'required': ['type', 'id']}
            components_schemas_dict[f'{f}_data_field']['properties'] = self._fields[f].get_data_field(record=self)
            components_schemas_dict['main_links_field'] = {
                'properties': {
                    'self': {
                        'type': 'string',
                        'format': 'uri',
                        'example': 'www.example.com/self_link'
                    },
                    'related': {
                        'type': 'string',
                        'format': 'uri',
                        'example': 'www.example.com/related_link'
                    }
                },
                'required': ['self', 'related']
            }

        return components_schemas_dict

    def generate_component_examples(self):
        components_examples_dict = {'examples': {}}
        components_examples_dict['examples'].update(self.generate_normal_post_request_example())
        components_examples_dict['examples'].update(self.generate_normal_patch_request_example())
        components_examples_dict['examples'].update(self.generate_relationships_post_manytomany_request_example())
        components_examples_dict['examples'].update(self.generate_relationships_post_onetomany_request_example())
        components_examples_dict['examples'].update(self.generate_relationships_patch_manytoone_request_example())
        components_examples_dict['examples'].update(self.generate_relationships_patch_manytoone_null_request_example())
        components_examples_dict['examples'].update(self.generate_relationships_patch_manytomany_request_example())
        components_examples_dict['examples'].update(self.generate_relationships_patch_manytomany_null_request_example())
        components_examples_dict['examples'].update(self.generate_relationships_patch_onetomany_request_example())
        components_examples_dict['examples'].update(self.generate_relationships_patch_onetomany_null_request_example())
        components_examples_dict['examples'].update(self.generate_relationships_delete_manytomany_request_example())
        components_examples_dict['examples'].update(self.generate_relationships_delete_onetomany_request_example())

        return components_examples_dict

    def generate_normal_post_request_example(self):
        data_dict = {
            "normal_post": {
                "data": {
                    "type": f"{self._name}",
                    "attributes": {
                        "normal_field_1": "normal_field_1_value",
                        "normal_field_2": "normal_field_2_value"
                    },
                    "relationships": {
                        "many_to_one_field": {
                            "data": {
                                "type": "many_to_one_field_model_name",
                                "id": "many_to_one_field_id"
                            }
                        },
                        "many_to_many_field": {
                            "data": [
                                {
                                    "type": "many_to_many_field_model_name",
                                    "id": "many_to_many_field_id_1"
                                },
                                {
                                    "type": "many_to_many_field_model_name",
                                    "id": "many_to_many_field_id_2"
                                }
                            ]
                        },
                        "one_to_many_field": {
                            "data": [
                                {
                                    "type": "one_to_many_field_model_name",
                                    "attributes": {
                                        "field_1": "field_1_value",
                                        "field_2": "field_2_value"
                                    }
                                },
                                {
                                    "type": "one_to_many_field_model_name",
                                    "attributes": {
                                        "field_1": "field_1_value",
                                        "field_2": "field_2_value"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
        return data_dict

    def generate_normal_patch_request_example(self):
        data_dict = {
            "normal_patch": {
                "data": {
                    "type": f"{self._name}",
                    "id": 12,
                    "attributes": {
                        "normal_field_1": "normal_field_1_value",
                        "normal_field_2": "normal_field_2_value"
                    },
                    "relationships": {
                        "many_to_one_field": {
                            "data": {
                                "type": "many_to_one_field_model_name",
                                "id": "many_to_one_field_id"
                            }
                        },
                        "many_to_many_field": {
                            "data": [
                                {
                                    "type": "many_to_many_field_model_name",
                                    "id": "many_to_many_field_id_1"
                                },
                                {
                                    "type": "many_to_many_field_model_name",
                                    "id": "many_to_many_field_id_2"
                                }
                            ]
                        },
                        "one_to_many_field": {
                            "data": [
                                {
                                    "type": "one_to_many_field_model_name",
                                    "attributes": {
                                        "field_1": "field_1_value",
                                        "field_2": "field_2_value"
                                    }
                                },
                                {
                                    "type": "one_to_many_field_model_name",
                                    "attributes": {
                                        "field_1": "field_1_value",
                                        "field_2": "field_2_value"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
        return data_dict

    def generate_relationships_post_manytomany_request_example(self):
        data_dict = {
            "relationships_post_manytomany": {
                "value":{
                'data': [
                        {
                            "type": "relational_field_model_name",
                            "id": "9"
                        },
                        {
                            "type": "relational_field_model_name",
                            "id": "10"
                        },
                        {
                            "type": "relational_field_model_name",
                            "id": "4"
                        }
                    ]
                },
                "description": "relationships model post operations many2many"
            }
        }
        return data_dict

    def generate_relationships_post_onetomany_request_example(self):
        data_dict = {
            "relationships_post_onetomany": {
                "value": {
                "data": [
                    {
                        "type": "relational_field_model_name",
                        "attributes": {
                            "product_id": 8,
                            "product_uom_qty": "2",
                            "price_unit": "6.75"
                        }
                    },
                    {
                        "type": "relational_field_model_name",
                        "attributes": {
                            "product_id": 18,
                            "product_uom_qty": "4",
                            "price_unit": "4.25"
                        }
                    }
                ]
                },
                "description": "relationships model post operations one2many"
            }
        }
        return data_dict

    def generate_relationships_patch_manytoone_request_example(self):
        data_dict = {
            "relationships_patch_manytoone": {
                "value": {
                    "data": {
                        "type": "relational_field_model_name",
                        "id": 34
                    }
                },
                "description": "relationships model patch operations many2one"
            }
        }
        return data_dict

    def generate_relationships_patch_manytoone_null_request_example(self):
        data_dict = {
            "relationships_patch_manytoone_null": {
                "value": {
                    "data": None
                },
                "description": "relationships model patch operations many2one with null value"
            }
        }
        return data_dict

    def generate_relationships_patch_manytomany_request_example(self):
        data_dict = {
            "relationships_patch_manytomany": {
                "value":{
                    'data': [
                        {
                            "type": "relational_field_model_name",
                            "id": 10
                        },
                        {
                            "type": "relational_field_model_name",
                            "id": 4
                        }
                    ],
                },
                "description": "relationships model patch operations many2many"
            }
        }
        return data_dict

    def generate_relationships_patch_manytomany_null_request_example(self):
        data_dict = {
            "relationships_patch_manytomany_null": {
                "value":{
                    'data': [],
                },
                "description": "relationships model patch operations many2many with null value"
            }
        }
        return data_dict

    def generate_relationships_patch_onetomany_request_example(self):
        data_dict = {
            "relationships_patch_onetomany": {
                "value": {
                    "data": [
                        {
                            "type": "relational_field_model_name",
                            "id": "119",
                            "attributes": {
                                "product_uom_qty": "120",
                                "price_unit": "40.75"
                            }
                        },
                        {
                            "type": "relational_field_model_name",
                            "attributes": {
                                "product_id": 33,
                                "product_uom_qty": "4",
                                "price_unit": "1200.75"
                            }
                        }
                    ]
                },
                "description": "relationships model patch operations one2many"
            }
        }
        return data_dict

    def generate_relationships_patch_onetomany_null_request_example(self):
        data_dict = {
            "relationships_patch_onetomany_null": {
                "value":{
                    'data': [],
                },
                "description": "relationships model patch operations one2many with null value"
            }
        }
        return data_dict

    def generate_relationships_delete_manytomany_request_example(self):
        data_dict = {
            "relationships_delete_manytomany": {
                "value": {
                    "data": [
                        {
                            "type": "relational_field_model_name",
                            "id": 1
                        },
                        {
                            "type": "relational_field_model_name",
                            "id": 2
                        }
                    ]
                },
                "description": "relationships model delete operations manytomany"
            }
        }

        return data_dict

    def generate_relationships_delete_onetomany_request_example(self):
        data_dict = {
            "relationships_delete_onetomany": {
                "value": {
                    "data": [
                        {
                            "type": "relational_field_model_name",
                            "id": 5
                        },
                        {
                            "type": "relational_field_model_name",
                            "id": 8
                        }
                    ]
                },
                "description": "relationships model delete operations onetomany"
            }
        }

        return data_dict

    def generate_components(self):
        component_dict = {}
        component_dict.update(self.generate_openapi_components_schemas())
        component_dict.update(self.generate_component_examples())
        return component_dict

    def generate_tags(self):
        return {
            'name': self._name,
            'description': f'<SchemaDefinition schemaRef="#/components/schemas/{self._name}" />'
        }

    def generate_paths(self, base_endpoint):
        data_dict = {
            f'/{base_endpoint}/{self._name}': {},
            f'/{base_endpoint}/{self._name}/{{id}}': {},
            f'/{base_endpoint}/{self._name}/{{id}}/relationships/{{model_field}}': {},
            }
        data_dict[f'/{base_endpoint}/{self._name}'].update(self.generate_model_get_path())
        data_dict[f'/{base_endpoint}/{self._name}'].update(self.generate_model_post_path())
        data_dict[f'/{base_endpoint}/{self._name}/{{id}}'].update(self.generate_model_id_get_path())
        data_dict[f'/{base_endpoint}/{self._name}/{{id}}'].update(self.generate_model_id_patch_path())
        data_dict[f'/{base_endpoint}/{self._name}/{{id}}'].update(self.generate_model_id_delete_path())
        data_dict[f'/{base_endpoint}/{self._name}/{{id}}/relationships/{{model_field}}'].update(self.generate_model_id_relationships_get_path())
        data_dict[f'/{base_endpoint}/{self._name}/{{id}}/relationships/{{model_field}}'].update(self.generate_model_id_relationships_post_path())
        data_dict[f'/{base_endpoint}/{self._name}/{{id}}/relationships/{{model_field}}'].update(self.generate_model_id_relationships_patch_path())
        data_dict[f'/{base_endpoint}/{self._name}/{{id}}/relationships/{{model_field}}'].update(self.generate_model_id_relationships_delete_path())

        return data_dict

    def generate_model_id_relationships_get_path(self):
        data_dict = {
            "get": {
                'tags': [f'{self._name}'],
                'summary': f'Fetch the {self._name} model data for particular id for particular relationships field',
                'description': f'Fetch {self._name} model record according to requeirements and for particular relationships field',
                'operationId': f'Get_Relationships_{self._name}_Model_Id',
                'parameters': [
                    {
                        'name': 'Content-Type',
                        'in': 'header',
                        'schema': {'type': 'string', 'default': 'application/vnd.api+json'},
                        'required': True
                    },
                    {
                        "name": "id",
                        "in": "path",
                        'required': True,
                        "schema": {"type": "integer", "format": "int32", "default": 12},
                    },
                    {
                        "name": "model_field",
                        "in": "path",
                        "schema": {
                            "type": "string",
                            "examples": ['model_relational_field_1', 'model_relational_field_2']
                        },
                        "required": True
                    },
                    {
                        'name': f'fields[relational_field_model_name]',
                        'in': 'query',
                        "description": "Describe fields name of particular model that you want to display",
                        'schema': {'type': 'string', 'examples': ['field_1', 'field_2', 'field_1,field_2']}
                    },
                    {
                        'name': 'include',
                        'in': 'query',
                        "description": "Name of relational-field for which you want to display data",
                        'schema': {'type': 'string', 'examples': ['relational_field_1', 'relational_field_1, relational_field_2']}
                    },
                ],
                'requestBody': {
                    'description': 'Nothing to provide in request body',
                    'content':{'application/vnd.api+json' : {'schema': {'type': 'object', 'example': None}}}
                },
                'responses': {
                    '200': {
                        'description': 'Successful Operation',
                        'content': {
                            'application/vnd.api+json': {'schema': {'type': 'object', 'example': {'data': 'data in the form of json-api'}}}
                        }
                    },
                    '4XX': {
                        'description': 'Errors'
                    }
                }
            }
        }

        return data_dict

    def generate_model_id_relationships_post_path(self):
        data_dict = {
            "post": {
                'tags': [f'{self._name}'],
                'summary': f'To Add {self._name} model record of realtionships link for model-field',
                'description': f'Add Record For Particular Model of realtionships link for model-field',
                'operationId': f'Post_Relationships_{self._name}_Model_Id',
                'parameters': [
                    {
                        'name': 'Content-Type',
                        'in': 'header',
                        'schema': {'type': 'string', 'default': 'application/vnd.api+json'},
                        'required': True
                    },
                    {
                        "name": "id",
                        "in": "path",
                        'required': True,
                        "schema": {"type": "integer", "format": "int32", "default": 12},
                    },
                    {
                        "name": "model_field",
                        "in": "path",
                        "schema": {
                            "type": "string",
                            "examples": ['model_relational_field_1', 'model_relational_field_2']
                        },
                        "required": True
                    },
                ],
                'requestBody': {
                    'description': 'POST Relationships request body example',
                    'content':{'application/vnd.api+json' :{
                            'examples': {
                                'many2many': {"$ref": "#/components/examples/relationships_post_manytomany"},
                                'one2many': {"$ref": "#/components/examples/relationships_post_onetomany"}
                                }
                                }
                            }
                },
                'responses': {
                    '200': {
                        'description': 'Successful Operation',
                        'content': {
                            'application/vnd.api+json': {'schema': {'type': 'object', 'example': {'data': 'data in the form of json-api'}}}
                        }
                    },
                    '4XX': {
                        'description': 'Errors'
                    }
                }
            }
        }

        return data_dict

    def generate_model_id_relationships_patch_path(self):
        data_dict = {
            "patch": {
                'tags': [f'{self._name}'],
                'summary': f'To Update {self._name} model record of realtionships link for model-field',
                'description': f'Update Record For Particular Model of realtionships link for model-field',
                'operationId': f'Patch_Relationships_{self._name}_Model_Id',
                'parameters': [
                    {
                        'name': 'Content-Type',
                        'in': 'header',
                        'schema': {'type': 'string', 'default': 'application/vnd.api+json'},
                        'required': True
                    },
                    {
                        "name": "id",
                        "in": "path",
                        'required': True,
                        "schema": {"type": "integer", "format": "int32", "default": 12},
                    },
                    {
                        "name": "model_field",
                        "in": "path",
                        "schema": {
                            "type": "string",
                            "examples": ['model_relational_field_1', 'model_relational_field_2']
                        },
                        "required": True
                    },
                ],
                'requestBody': {
                    'description': 'PATCH Relationships request body example',
                    'content':{'application/vnd.api+json' :{
                            'examples': {
                                'many2one': {"$ref": "#/components/examples/relationships_patch_manytoone"},
                                'many2one null': {"$ref": "#/components/examples/relationships_patch_manytoone_null"},
                                'many2many': {"$ref": "#/components/examples/relationships_patch_manytomany"},
                                'many2many null': {"$ref": "#/components/examples/relationships_patch_manytomany_null"},
                                'one2many': {"$ref": "#/components/examples/relationships_patch_onetomany"},
                                'one2many null': {"$ref": "#/components/examples/relationships_patch_onetomany_null"}
                                }
                                }
                            }
                },
                'responses': {
                    '200': {
                        'description': 'Successful Operation',
                        'content': {
                            'application/vnd.api+json': {'schema': {'type': 'object', 'example': {'data': 'data in the form of json-api'}}}
                        }
                    },
                    '4XX': {
                        'description': 'Errors'
                    }
                }
            }
        }

        return data_dict

    def generate_model_id_relationships_delete_path(self):
        data_dict = {
            "delete": {
                'tags': [f'{self._name}'],
                'summary': f'To Delete {self._name} model record of realtionships link for model-field',
                'description': f'Update Delete For Particular Model of realtionships link for model-field',
                'operationId': f'Delete_Relationships_{self._name}_Model_Id',
                'parameters': [
                    {
                        'name': 'Content-Type',
                        'in': 'header',
                        'schema': {'type': 'string', 'default': 'application/vnd.api+json'},
                        'required': True
                    },
                    {
                        "name": "id",
                        "in": "path",
                        'required': True,
                        "schema": {"type": "integer", "format": "int32", "default": 12},
                    },
                    {
                        "name": "model_field",
                        "in": "path",
                        "schema": {
                            "type": "string",
                            "examples": ['model_relational_field_1', 'model_relational_field_2']
                        },
                        "required": True
                    },
                ],
                'requestBody': {
                    'description': 'DELETE Relationships request body example',
                    'content':{'application/vnd.api+json' :{
                            'examples': {
                                'many2many': {"$ref": "#/components/examples/relationships_delete_manytomany"},
                                'one2many': {"$ref": "#/components/examples/relationships_delete_onetomany"}
                                }
                                }
                            }
                },
                'responses': {
                    '200': {
                        'description': 'Successful Operation',
                        'content': {
                            'application/vnd.api+json': {'schema': {'type': 'object', 'example': {'data': 'data in the form of json-api'}}}
                        }
                    },
                    '4XX': {
                        'description': 'Errors'
                    }
                }
            }
        }

        return data_dict

    def generate_model_id_get_path(self):
        data_dict = {
            "get": {
                'tags': [f'{self._name}'],
                'summary': f'Fetch the {self._name} model data for particular Id',
                'description': f'Fetch {self._name} model id record according to requeirements',
                'operationId': f'Get_{self._name}_Model_Id',
                'parameters': [
                    {
                        'name': 'Content-Type',
                        'in': 'header',
                        'schema': {'type': 'string', 'default': 'application/vnd.api+json'},
                        'required': True
                    },
                    {
                        "name": "id",
                        "in": "path",
                        'required': True,
                        "schema": {"type": "integer", "format": "int32", "default": 12},
                    },
                    {
                        'name': f'fields[{self._name}]',
                        'in': 'query',
                        "description": "Describe fields name of particular model that you want to display",
                        'schema': {'type': 'string', 'examples': ['field_1', 'field_2', 'field_1,field_2']}
                    },
                    {
                        'name': 'include',
                        'in': 'query',
                        "description": "Name of relational-field for which you want to display data",
                        'schema': {'type': 'string', 'examples': ['relational_field_1', 'relational_field_2', 'relational_field_1,relational_field_2']}
                    },
                ],
                'requestBody': {
                    'description': 'Nothing to provide in request body',
                    'content':{'application/vnd.api+json' : {'schema': {'type': 'object', 'example': None}}}
                },
                'responses': {
                    '200': {
                        'description': 'Successful Operation',
                        'content': {
                            'application/vnd.api+json': {'schema': {'type': 'object', 'example': {'data': 'data in the form of json-api'}}}
                        }
                    },
                    '4XX': {
                        'description': 'Errors'
                    }
                }
            }
        }

        return data_dict

    def generate_model_id_patch_path(self):
        data_dict = {
            "patch": {
                'tags': [f'{self._name}'],
                'summary': f'To update {self._name} model record of particular Id',
                'description': f'Update record for {self._name} model of particular Id according to requeirements',
                'operationId': f'Patch_{self._name}_Model_Id',
                'parameters': [
                    {
                        'name': 'Content-Type',
                        'in': 'header',
                        'schema': {'type': 'string', 'default': 'application/vnd.api+json'},
                        'required': True
                    },
                    {
                        "name": "id",
                        "in": "path",
                        'required': True,
                        "schema": {"type": "integer", "format": "int32", "default": 12},
                    },
                ],
                'requestBody': {
                    'description': 'PATCH ID request body example',
                    'content':{'application/vnd.api+json' : {'schema': {'type': 'object'}, 'example': {"$ref": "#/components/examples/normal_patch"}}}
                },
                'responses': {
                    '200': {
                        'description': 'Successfully Operation',
                        'content': {
                            'application/vnd.api+json': {'schema': {'type': 'object', 'example': {"$ref": "#/components/examples/normal_patch"}}}
                        }
                    },
                    '4XX': {
                        'description': 'Errors'
                    }
                }
            }
        }
        return data_dict

    def generate_model_id_delete_path(self):
        data_dict = {
            "delete": {
                'tags': [f'{self._name}'],
                'summary': f'To delete {self._name} model record of particular Id',
                'description': f'Delete record for {self._name} model of particular Id',
                'operationId': f'Delete_{self._name}_Model_Id',
                'parameters': [
                    {
                        'name': 'Content-Type',
                        'in': 'header',
                        'schema': {'type': 'string', 'default': 'application/vnd.api+json'},
                        'required': True
                    },
                    {
                        "name": "id",
                        "in": "path",
                        'required': True,
                        "schema": {"type": "integer", "format": "int32", "default": 12},
                    },
                ],
                'requestBody': {
                    'description': 'DELETE ID request body example',
                    'content':{'application/vnd.api+json' : {'schema': {'type': 'object'}, 'example': None}}
                },
                'responses': {
                    '200': {
                        'description': 'Successfully Operation',
                        'content': {
                            'application/vnd.api+json': {'schema': {'type': 'object', 'example': None}}
                        }
                    },
                    '4XX': {
                        'description': 'Errors'
                    }
                }
            }
        }
        return data_dict

    def generate_model_post_path(self):
        data_dict = {
            "post": {
                'tags': [f'{self._name}'],
                'summary': f'To Create {self._name} model record',
                'description': f'Create record for {self._name} model according to requeirements',
                'operationId': f'Post_{self._name}_Model',
                'parameters': [
                    {
                        'name': 'Content-Type',
                        'in': 'header',
                        'schema': {'type': 'string', 'default': 'application/vnd.api+json'},
                        'required': True
                    },
                ],
                'requestBody': {
                    'description': 'POST request body example',
                    'content':{'application/vnd.api+json' : {'schema': {'type': 'object'}, 'example': {"$ref": "#/components/examples/normal_post"}}}
                },
                'responses': {
                    '201': {
                        'description': 'Successfully Created',
                        'content': {
                            'application/vnd.api+json': {'schema': {'type': 'object', 'example': {'data': None}}}
                        }
                    },
                    '4XX': {
                        'description': 'Errors'
                    }
                }
            }
        }
        return data_dict

    def generate_model_get_path(self):
        data_dict = {
            "get": {
                'tags': [f'{self._name}'],
                'summary': f'Fetch the {self._name} model data',
                'description': f'Fetch {self._name} model record according to requeirements',
                'operationId': f'Get_{self._name}_Model',
                'parameters': [
                    {
                        'name': 'Content-Type',
                        'in': 'header',
                        'schema': {'type': 'string', 'default': 'application/vnd.api+json'},
                        'required': True
                    },
                    {
                        'name': f'fields[{self._name}]',
                        'in': 'query',
                        "description": "Describe fields name of particular model that you want to display",
                        'schema': {'type': 'string', 'examples': ['field_1', 'field_2', 'field_1,field_2']}
                    },
                    {
                        'name': 'include',
                        'in': 'query',
                        "description": "Name of relational-field for which you want to display data",
                        'schema': {'type': 'string', 'examples': ['relational_field_1', 'relational_field_2', 'relational_field_1,relational_field_2']}
                    },
                    {
                        'name': 'page[size]',
                        'in': 'query',
                        "description": "Page Size describes how many record(s) you want to display per page",
                        'schema': {'type': 'string', 'example': '3'}
                    },
                    {
                        'name': 'page[number]',
                        'in': 'query',
                        "description": "It Defines Page number",
                        'schema': {'type': 'string', 'example': '2'}
                    },
                    {
                        'name': 'sort',
                        'in': 'query',
                        "description": "For which field you want record to be sorted",
                        'schema': {'type': 'string', 'examples': ['field_1', 'field_2', 'field_1,field_2']}
                    },
                    {
                        'name': 'filter',
                        'in': 'query',
                        "description": "Provide domain like standard odoo, just replace '|' with OR, '&' with AND",
                        'schema': {'type': 'string', 'examples': ["[('name','=','ABC'),('language.code','!=','en_US'),OR,('country_id.code','=','be'),('country_id.code','=','de')]", "[AND,('name','=','ABC'),('language.code','!=','en_US')]", "[('name','=','ABC'),('language.code','!=','en_US')]"]}
                    }
                ],
                'requestBody': {
                    'description': 'Nothing to provide in request body',
                    'content':{'application/vnd.api+json' : {'schema': {'type': 'object', 'example': None}}}
                },
                'responses': {
                    '200': {
                        'description': 'Successful Operation',
                        'content': {
                            'application/vnd.api+json': {'schema': {'type': 'object', 'example': {'data': 'data in the form of json-api'}}}
                        }
                    },
                    '4XX': {
                        'description': 'Errors'
                    }
                }
            }
        }

        return data_dict
