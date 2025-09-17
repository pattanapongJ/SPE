"""Test-API Controllers"""

import json
from werkzeug.datastructures import Headers
from odoo import http
from odoo.http import request, Response

class JsonAPIDocumnetations(http.Controller):

    @http.route(
        ['/<api>/jsonapidoc/<doc_id>'],
        auth='user',
        csrf=False,
    )
    def jsonApiDocController(self, doc_id, uri=None, **kwargs):
        return f"""
<html>
  <head>
    <title>Redoc</title>
    <!-- needed for adaptive design -->
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link
      href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700"
      rel="stylesheet"
    />

    <!--
    Redoc doesn't change outer page styles
    -->
    <style>
      body {{
        margin: 0;
        padding: 0;
      }}
    </style>
  </head>
  <body>
    <!--
    Redoc element with link to your OpenAPI definition
    -->
    <redoc spec-url="/openapidoc/{doc_id}"></redoc>
    <!--
    Link to Redoc JavaScript on CDN for rendering standalone element
    -->
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
  </body>
</html>
        """

    def generate_main_info(self):
        main_dict = {
            "openapi": "3.1.0",
            "info": {
                "title": "Odoo JSON API",
                "description": "This is description of Odoo JSON-API ",
                "termsOfService": "http://www.example.com/terms",
                "version": "1.0.11"
            }
        }

    @http.route(
    ['/openapidoc/<doc_id>'],
    auth='user',
    csrf=False,
    )
    def DocController(self, doc_id, uri=None, **kwargs):
        doc = request.env['easy.jsonapi.doc'].search([('id','=',doc_id)])
        doc_models = [v.model for v in doc.model_ids]
        main_document = {
            "openapi": "3.1.0",
            "info": {
                "title": "Odoo JSON API",
                "description": "This is description of Odoo JSON-API ",
                "termsOfService": "http://www.example.com/terms",
                "version": "1.0.11"
            },
            'tags': [],
            'paths': {},
            'components': {'schemas': {}}
        }
        for model in doc_models:
            modelObj = request.env[model]
            tag_lists = modelObj.generate_tags()
            path_dict = modelObj.generate_paths(doc.easy_api_id.base_endpoint)
            components_schemas = modelObj.generate_components()
            main_document['tags'].append(tag_lists)
            main_document['paths'].update(path_dict)
            main_document['components']['schemas'].update(components_schemas)

        data = json.dumps(main_document, ensure_ascii=False)
        headers = Headers()
        headers['Content-Length'] = len(data)
        return Response(data, headers=headers ,status=200)

