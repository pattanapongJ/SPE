# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

import json
from uuid import uuid4
from base64 import b64encode
from odoo import models
from odoo.addons.web.controllers.main import ExportFormat, ExcelExport


class EasyapiGraphqlExport(models.AbstractModel):
    _name = 'easyapi.graphql.export'
    _description = "GraphQL Export Data"

    def generate_export_format(self):
        export_format = ExportFormat()
        export_format.from_data = ExcelExport.from_data
        export_format.from_group_data = ExcelExport.from_group_data
        export_format.content_type = ExcelExport.content_type
        return export_format

    def handle_graphql_export(self, values, variables):
        export_format = GraphQLCustomExportFormat()
        random_token = str(uuid4())
        # Provide export input data in variable
        variable_name = values['arguments'][0]['value']['name']['value']
        variable_value = variables.get(variable_name)
        result = export_format.base(json.dumps(variable_value), random_token)
        alias = values['alias']
        display_key = alias['value'] if alias else values['name']['value']
        result_data = f'{{"data": {{"{display_key}": "{b64encode(result.data).decode()}"}}}}'
        result.data = result_data.encode()
        return result

class GraphQLCustomExportFormat(ExportFormat):

    @property
    def content_type(self):
        return ExcelExport().content_type
    
    def filename(self, base):
        return ExcelExport.filename(self, base)

    def from_data(self, fields, rows):
        return ExcelExport.from_data(self, fields, rows)

    def from_group_data(self, fields, rows):
        return ExcelExport.from_group_data(self, fields, rows)
