from odoo.fields import (_Relational,Float, Monetary, Integer,
                        Selection, Char, Text, Date,
                        Datetime, Html, Boolean, Binary, Id, Field)

def get_schema_properties_id(self, record):
    """
    record is model record
    """
    data = {'type': 'integer', 'example':125}
    return data

def get_schema_properties_float(self, record):
    """
    record is model record
    """
    data = {'type': 'number', 'example':12.435}
    return data

def get_schema_properties_monetary(self, record):
    """
    record is model record
    """
    data = {'type': 'number', 'example': 12.435}
    return data

def get_schema_properties_integer(self, record):
    """
    record is model record
    """
    data = {'type': 'integer', 'example': 12}
    return data


def get_schema_properties_char(self, record):
    """
    record is model record
    """
    data = {'type': 'string', 'example': 'string value'}
    return data

def get_schema_properties_field(self, record):
    """
    record is model record
    """
    data = {'type': 'string', 'example': 'string value'}
    return data


def get_schema_properties_text(self, record):
    """
    record is model record
    """
    data = {'type': 'string', 'example': 'string value'}
    return data


def get_schema_properties_html(self, record):
    """
    record is model record
    """
    data = {'type': 'string', 'example': 'string value'}
    return data


def get_schema_properties_date(self, record):
    """
    record is model record
    """
    data = {'type': 'string', 'example': "date-format: %Y-%m-%d", 'format': "%Y-%m-%d"}
    return data


def get_schema_properties_datetime(self, record):
    """
    record is model record
    """
    data = {'type': 'string',
            'example': 'date-time-format: %Y-%m-%d %H:%M:%S',
            'format': "%Y-%m-%d %H:%M:%S"}
    return data

def get_schema_properties_selection(self, record):
    """
    record is model record
    """
    return {'type': 'string', 'enum': self.get_values(record.env)}

def get_schema_properties_boolean(self, record):
    """
    record is model record
    """
    data = {'type': 'boolean', 'example': True}
    return data

def get_schema_properties_binary(self, record):
    """
    record is model record
    """
    data = {'type': 'string', 'example': True}
    return data

def get_schema_properties_relational(self, record):
    """
    record is model record
    """
    data = {
        '$ref': f'#/components/schemas/relationships_{self.name}_data',
        'type': 'object'
    }
    return data

def get_relationships_field_data(self, record):
    if self.type == 'many2one':
        data = {
            'links': {
                'type': 'object',
                '$ref': f'#/components/schemas/main_links_field'
            },
            'data': {
                'type': 'object',
                '$ref': f'#/components/schemas/{self.name}_data_field',
            }
        }
        return data
    else:
        data = {
            'links': {
                'type': 'object',
                '$ref': f'#/components/schemas/main_links_field'
            },
            'data': {
                'type': 'array',
                'items': {
                    '$ref': f'#/components/schemas/{self.name}_data_field',
                }
            }
        }
        return data

def get_data_field(self, record):
    data = {
        'type': {
            'type': 'string',
            'example': record[self.name]._name
        },
        'id': {
            'type': 'integer',
            'example': 1234
        }
    }
    return data

_Relational.get_schema_properties = get_schema_properties_relational
_Relational.get_relationships_field_data = get_relationships_field_data
_Relational.get_data_field = get_data_field

Float.get_schema_properties = get_schema_properties_float
Monetary.get_schema_properties = get_schema_properties_monetary
Integer.get_schema_properties = get_schema_properties_integer
Char.get_schema_properties = get_schema_properties_char
Text.get_schema_properties = get_schema_properties_text
Html.get_schema_properties = get_schema_properties_html
Date.get_schema_properties = get_schema_properties_date
Datetime.get_schema_properties = get_schema_properties_datetime
Selection.get_schema_properties = get_schema_properties_selection
Boolean.get_schema_properties = get_schema_properties_boolean
Binary.get_schema_properties = get_schema_properties_binary
Id.get_schema_properties = get_schema_properties_id
Field.get_schema_properties = get_schema_properties_field
