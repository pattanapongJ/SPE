# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

"""Test-API Controllers"""

import json
from uuid import uuid4
from base64 import b64encode
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import ExcelExport


class JsonAPI(ExcelExport, http.Controller):

    @http.route(
        ['/_jsonapi_dynamic_api_route'],
        auth='api',
        csrf=False,
        methods=['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
        cors='api',
        save_session=False
    )
    def jsonApiGetController(self):
        return request.env['easy.jsonapi'].serve()
    #add This in version-15 in version-16 type= api
    @http.route('/_jsonapi_dynamic_api_route/export', auth="api", cors='api', save_session=False)
    def jsonApiExport(self):
        data = json.loads(request.httprequest.get_data(as_text=True))
        try:
            random_token = str(uuid4())
            result = self.base(json.dumps(data), random_token)
            result.is_api = False
            result_data = f'{{"file_data": "{b64encode(result.data).decode()}"}}'
            result.data = result_data.encode()
            return result
        except Exception as exc:
            raise exc

    @http.route('/_jsonapi_dynamic_api_route/report', cors='api', auth="api", save_session=False)
    def jsonApiReport(self):
        values = json.loads(request.httprequest.get_data(as_text=True))
        if not values.get('converter') and not values.get('report_ref'):
            raise Exception('Provide inputs')
        try:
            converter = values.get('converter')
            report_ref = values.get('report_ref')
            res_ids = values.get('res_ids')
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
