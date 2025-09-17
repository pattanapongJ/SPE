# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import api, models
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError
from odoo.addons.ekika_utils.tools.jsonapi_exceptions import (ValidationError as JsonApiValidationError)



def build_relationships(field, fieldvalue, fieldmodel, selflink=None):
    """Building relationships node of jsonapi resource top level. Can be used
    for include and don't provide link of self will do the job.

    :param field (str) field name of the relational field.
    :param fieldvalue (id OR list of ids as int) value of the relational field.
    :param fieldmodel (str) comodel name of the relational field.
    :param selflink (str) jsonapi link for the current record.
    :returns relationships's value as
        {
            "author": {
                "links": {
                    "self": "/articles/1/relationships/author",
                    "related": "/articles/1/author"
                },
                "data": { "type": "people", "id": "9" }
            }
        }
    """
    if hasattr(fieldvalue, '__iter__'):  # When multi relationships
        if selflink:
            return {
                "links": {
                    "self": f"{selflink}/relationships/{field}",
                    "related": f"{selflink}/{field}",
                    "describedby": request.easyapi['meta_documentation_link']
                },
                "data":  [{'type': fieldmodel, 'id': j} for j in fieldvalue] if fieldvalue else None
            }
        else:
            return {
                "data":  [{'type': fieldmodel, 'id': j} for j in fieldvalue] if fieldvalue else None
            }

    if selflink:
        return {
            "links": {
                "self": f"{selflink}/relationships/{field}",
                "related": f"{selflink}/{field}",
                "describedby": request.easyapi['meta_documentation_link']
            },
            "data": {
                "type": fieldmodel,
                "id": fieldvalue
            } if fieldvalue else None
        }
    else:
        return {
            "data": {
                "type": fieldmodel,
                "id": fieldvalue
            } if fieldvalue else None
        }


class Base(models.AbstractModel):
    """JSON:API model conversion.

    Resource Objects
    ----------------
    "Resource objects" appear in a JSON:API document to represent resources.

    A resource object MUST contain at least the following top-level members:
        - id
        - type

    Exception: The id member is not required when the resource object
    originates at the client and represents a new resource to be created on
    the server. In that case, a client MAY include a lid member to uniquely
    identify the resource by type locally within the document.

    In addition, a resource object MAY contain any of these top-level members:
        - attributes: an attributes object representing some of the resource's
        data.
        - relationships: a relationships object describing relationships
        between the resource and other JSON:API resources.
        - links: a links object containing links related to the resource.
        - meta: a meta object containing non-standard meta-information about
        a resource that can not be represented as an attribute or relationship.

    Here's how an article (i.e. a resource of type "articles") might appear in
    a document:

    // ...
    {
        "type": "articles",
        "id": "1",
        "attributes": {
            "title": "Rails is Omakase"
        },
        "relationships": {
            "author": {
                "links": {
                    "self": "/articles/1/relationships/author",
                    "related": "/articles/1/author"
                },
                "data": { "type": "people", "id": "9" }
            }
        }
    }
    // ...

    """
    _inherit = 'base'

    @api.model
    def seperate_relational_fields(self, fields):
        """Seperates simple fields and relational fields.

        :param fields (required): list of fields of self for identification.

        :return simple-fields, relational-fields (Note: simple-fields as list
        and relational fields as dict where keys are field and values are comodel name.)
        """
        simple = []
        relational = {}
        for fld in fields or []:
            if fld in self._fields:
                if self._fields[fld].comodel_name:
                    relational[fld] = self._fields[fld].comodel_name
                else:
                    simple.append(fld)
            else:
                raise JsonApiValidationError(f"Field:'{fld}' not found on model:'{self._name}'")
        return simple, relational

    @api.model
    def jsonapi_read(self, fields, link_prefix, relationships_links=True, self_link=True):
        """
        Performs your search on the model and call this read to get jsonapi
        formated resources.

        :param fields (required): all list of fields to read
        :param link_prefix (required): url decided by framework as prefix.
        :param relationships_links (optional): jsonapi's include does not
        require self & related links of include's relationships. So in that
        case relationships_links=False is used.

        :return: [
            {
                "type": "res.partner",
                "id": "1",
                "attributes": {
                    "name": "Anand Shukla",
                    "active": true,
                    "type": "contact"
                },
                "relationships": {
                    "parent_id": {

                        // Does not provided when relationships_links=False
                        "links": {
                            "self": "/res.partner/1/relationships/partner_id",
                            "related": "/res.partner/1/partner_id"
                        },

                        "data": {"type": "res.partner", "id": "2"}
                    }
                },
                "links": {
                    "self": "/res.partner/1"
                }
            },
            ...
        ]
        """
        simple, relational = self.seperate_relational_fields(fields)
        selfurl = f"{link_prefix}/{self._name}/{{}}"
        selfname = self._name
        return [{
            'type': selfname,
            'id': record['id'],
            'attributes': {field: record[field] for field in simple},
            'relationships': {
                field: build_relationships(
                    field, record[field], fieldmodel,
                    selflink=selfurl.format(record['id']) if relationships_links else None
                ) for field, fieldmodel in relational.items()
            },
            'links': {'self': selfurl.format(record['id'])} if self_link else None
        } for record in self.read(fields, load='') ]

    def generate_create_field_values(self, data):
        values = {}
        if data.get('data').get('attributes'):
            values.update(data['data']['attributes'])

        if 'relationships' in data['data']:
            relational_fields = [k  for key,val in data.items()
                                 if isinstance(val,dict) for k,v in val['relationships'].items()]
            for field in relational_fields:
                value = self._fields[field].json_api_prepare_create_value(data=data)
                values.update(value)
        return values

    def perform_create_operation(self, data):
        vals = self.generate_create_field_values(data=data)
        try:
            new_data = self.create(vals)
        except Exception as exc:
            raise exc
        else:
            return new_data

    def generate_write_fields_values(self, data, relationships=None, model_field=None, method=None):
        if relationships:
            values = self._fields[model_field]\
                .json_api_prepare_relationship_write_value(data=data, record=self, method=method)
            return values
        else:
            values = {}
            if data.get('data').get('attributes'):
                values.update(data['data']['attributes'])

            if 'relationships' in data['data']:
                relational_fields = [k  for key,val in data.items()
                                     if isinstance(val,dict)
                                     for k,v in val['relationships'].items()]
                for field in relational_fields:
                    value = self._fields[field].json_api_prepare_write_value(data=data, record=self)
                    values.update(value)
            return values

    def perform_write_operation(self, data, relationships=None, model_field=None, method=None):
        vals = self.generate_write_fields_values(data=data, relationships=relationships,
                                                 model_field=model_field, method=method)
        try:
            self.write(vals)
        except Exception as exc:
            raise exc

    def perform_delete_operation(self):
        try:
            self.unlink()
        except Exception as exc:
            raise exc
        else:
            return

