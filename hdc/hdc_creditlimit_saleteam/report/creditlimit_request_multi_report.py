
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools.translate import translate
from odoo.tools import format_date

import io
import base64
import xlsxwriter
import re

from datetime import datetime, timedelta
import calendar

class CreditlimitRequestMultiReport(models.AbstractModel):
    _name = 'report.hdc_creditlimit_saleteam.hdc_tcr_multi_report'
    _description = 'Creditlimit Request Multi Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        temp_credit_ids = self.env["temp.credit.request"].search([('id', 'in', data.get('temp_credit_ids'))],order='create_date desc')
        main_request = temp_credit_ids[0]
        check_request = temp_credit_ids[1:]
        docs = self.env['temp.credit.request'].browse(main_request.id)
        request_list = []
        project_name_list = ""
        count = 0
        so_name1 = ""
        so_name2 = ""
        reason_approval_list = ""
        total1 = 0
        total2 = 0
        if main_request.reason_approval:
            reason_approval_list = main_request.reason_approval
        for request in check_request:
            count += 1
            if count %2 == 1:
                so_name1 = request.order_no.name
                total1 = request.remain_amount
            if count %2 == 0:
                so_name2 = request.order_no.name
                total2 = request.remain_amount
                request_list.append([2,so_name1,total1,so_name2,total2,])
            if request.order_no.project_name:
                if len(project_name_list) == 0:
                    project_name_list = request.order_no.project_name.project_name
                else:
                    project_name_list = project_name_list + "," + request.order_no.project_name.project_name
            if request.reason_approval:
                if len(reason_approval_list) == 0:
                    reason_approval_list = request.reason_approval
                else:
                    reason_approval_list = reason_approval_list + "," + request.reason_approval
        if count %2 == 1:
            request_list.append([1,so_name1,total1])
        request_box = []
        request_box = [request_list[i:i+5] for i in range(0, len(request_list), 5)]
        report_values = {
            'docs':docs,
            'request_box':request_box,
            'project_name_list':project_name_list,
            'reason_approval_list':reason_approval_list,
        }
        
        return report_values