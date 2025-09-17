# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

QUERY_MODEL_ARGS = [
    {
    "name": "id",
    "description": None,
    "type": {
        "kind": "SCALAR",
        "name": "ID",
        "ofType": None
        },
    "defaultValue": None
    },
    {
    'name': 'domain',
    'description': 'Pass Domain Like Standard Odoo.',
    'type': {
        'kind': 'LIST',
        'name':None,
        "ofType": {
            "kind": "LIST",
            "name": None,
            "ofType": {
                "kind": "SCALAR",
                "name": "Any",
                "ofType": None
            }
        }
    },
    'defaultValue': None
    },
    {
    "name": "limit",
    "description": None,
    "type": {
        "kind": "SCALAR",
        "name": "Int",
        "ofType": None
        },
    "defaultValue": None
    },
    {
    "name": "offset",
    "description": None,
    "type": {
        "kind": "SCALAR",
        "name": "Int",
        "ofType": None
        },
    "defaultValue": None
    },
    {
    "name": "order",
    "description": None,
    "type": {
        "kind": "SCALAR",
        "name": "String",
        "ofType": None
        },
    "defaultValue": None
    }
]

TYPES_DATA = [
    {
        "kind": "SCALAR",
        "name": "ID",
        "description": "The ID scalar type represents a unique identifier, often used to refetch an object or as the key for a cache. The ID type is serialized in the same way as a String; however, defining it as an ID signifies that it is not intended to be human-readable.",
        "fields": None,
        "inputFields": None,
        "interfaces": None,
        "enumValues": None,
        "possibleTypes": None
    },
    {
        "kind": "SCALAR",
        "name": "String",
        "description": "The String type of scalar",
        "fields": None,
        "inputFields": None,
        "interfaces": None,
        "enumValues": None,
        "possibleTypes": None
    },
    {
        "kind": "SCALAR",
        "name": "Boolean",
        "description": "The Boolean scalar type represents true or false.",
        "fields": None,
        "inputFields": None,
        "interfaces": None,
        "enumValues": None,
        "possibleTypes": None
    },
    {
        "kind": "SCALAR",
        "name": "Int",
        "description": " A signed 32-bit integer",
        "fields": None,
        "inputFields": None,
        "interfaces": None,
        "enumValues": None,
        "possibleTypes": None
    },
    {
        "kind": "SCALAR",
        "name": "Float",
        "description": "The Float type of scalar",
        "fields": None,
        "inputFields": None,
        "interfaces": None,
        "enumValues": None,
        "possibleTypes": None
    },
    {
        "kind": "SCALAR",
        "name": "Any",
        "description": "The Boolean scalar type represents true or false.",
        "fields": None,
        "inputFields": None,
        "interfaces": None,
        "enumValues": None,
        "possibleTypes": None
    },
]

DIRECTIVES_DATA = [
    {
        "name": "include",
        "description": "Conditionally include a field in the result based on the provided Boolean condition. If the condition is true, the field will be included in the response. This directive is often used in combination with variables to make queries more dynamic.",
        "locations": [
        "FIELD",
        "FRAGMENT_SPREAD",
        "INLINE_FRAGMENT"
        ],
        "args": [
        {
            "name": "if",
            "description": "Include when true.",
            "type": {
            "kind": "NON_NULL",
            "name": None,
            "ofType": {
                "kind": "SCALAR",
                "name": "Boolean",
                "ofType": None
            }
            },
            "defaultValue": None
        }
        ]
    },
    {
        "name": "skip",
        "description": "Conditionally exclude a field from the result based on the provided Boolean condition. If the condition is true, the field will be skipped and not included in the response.",
        "locations": [
        "FIELD",
        "FRAGMENT_SPREAD",
        "INLINE_FRAGMENT"
        ],
        "args": [
        {
            "name": "if",
            "description": "Skip when true.",
            "type": {
            "kind": "NON_NULL",
            "name": None,
            "ofType": {
                "kind": "SCALAR",
                "name": "Boolean",
                "ofType": None
            }
            },
            "defaultValue": None
        }
        ]
    },
]
