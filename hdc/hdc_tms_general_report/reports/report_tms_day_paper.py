
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

class ReportTmsDayPaper(models.AbstractModel):
    _name = 'report.hdc_tms_general_report.tms_day_report'
    _description = 'Report TMS Day'

    @api.model
    def _get_report_values(self, docids, data=None):

        keep_transport_line_code = []
        keep_driver_line_name = []

        driver_ids = re.findall(r'\d+', data['driver_ids'])
        driver_ids = [int(id_) for id_ in driver_ids]

        ids = re.findall(r'\d+', data['transport_desc_ids'])
        ids = [int(id_) for id_ in ids]

        for transport_desc in ids:
            if transport_desc:
                trans_code = self.env['delivery.round'].browse(transport_desc)
                keep_transport_line_code.append(trans_code.code)
        
        for driver_id in driver_ids:
            if driver_id:
                driver_name = self.env['driver.model'].browse(driver_id)
                keep_driver_line_name.append(driver_name.name)

        keep_billing_status = []
        billing_ids = re.findall(r'\d+', data['billing_status'])
        billing_ids = [int(id_) for id_ in billing_ids]
        for billing in billing_ids:
            if billing:
                billing_status = self.env['billing.status.tms'].browse(billing)
                keep_billing_status.append(billing_status.code)

        keep_delivery_status = []
        delivery_ids = re.findall(r'\d+', data['delivery_status'])
        delivery_ids = [int(id_) for id_ in delivery_ids]
        for delivery in delivery_ids:
            if delivery:
                delivery_status = self.env['delivery.status.tms'].browse(delivery)
                keep_delivery_status.append(delivery_status.code)
        
        domain = [
            ('delivery_date', '>=', data['from_date']),
            ('delivery_date', '<=', data['to_date'])
        ]

        if keep_transport_line_code:
            domain.append(('transport_desc', 'in', keep_transport_line_code))

        if keep_driver_line_name:
            domain.append(('driver_id.name', 'in', keep_driver_line_name))

        if keep_billing_status:
            domain.append(('invoice_line_ids.billing_status', 'in', keep_billing_status))

        if keep_delivery_status:
            domain.append(('invoice_line_ids.delivery_status', 'in', keep_delivery_status))
        
        if data['tms_remark']:
            domain.append(('invoice_line_ids.tms_remark', '=', data['tms_remark']))

        distribution_deli_notes = self.env["distribition.delivery.note"].search(domain)

        sum_count = 0
        total_price = 0

        for line in distribution_deli_notes:
            invoice_line = line.invoice_line_ids
            if data['tms_remark']:
                invoice_line = invoice_line.filtered(lambda x: x.tms_remark == data['tms_remark'])
            sum_count += len(invoice_line)
            for invoice in invoice_line:
                total_price += invoice.amount_total

        from_date = fields.Date.from_string(data['from_date'])
        to_date = fields.Date.from_string(data['to_date'])

        str_from_date = from_date.strftime('%d-%m-%Y')
        str_to_date = to_date.strftime('%d-%m-%Y')

        now = datetime.now() + timedelta(hours=7)

        formatted_date = format_date(self.env, now.date(), date_format="d MMMM yyyy", lang_code="th_TH")

        buddhist_year = now.year + 543
        formatted_date = formatted_date.replace(str(now.year), str(buddhist_year))

        thai_months = {
            'January': 'มกราคม',
            'February': 'กุมภาพันธ์',
            'March': 'มีนาคม',
            'April': 'เมษายน',
            'May': 'พฤษภาคม',
            'June': 'มิถุนายน',
            'July': 'กรกฎาคม',
            'August': 'สิงหาคม',
            'September': 'กันยายน',
            'October': 'ตุลาคม',
            'November': 'พฤศจิกายน',
            'December': 'ธันวาคม'
        }

        month_name = calendar.month_name[now.month]
        formatted_date = formatted_date.replace(str(month_name), thai_months.get(month_name, month_name))

        formatted_time = now.strftime('%H:%M')

        report_values = {
            'from_date': str_from_date,
            'to_date': str_to_date,
            # 'list_driver': list_driver,
            'distribution_deli_notes': distribution_deli_notes,
            'sum_count': sum_count,
            'total_price': total_price,
            'formatted_date': formatted_date,
            'formatted_time': formatted_time
        }

        return report_values