
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools.translate import translate

import io
import base64
import xlsxwriter

import re

class ReportTmsAllPaper(models.AbstractModel):
    _name = 'report.hdc_tms_general_report.hdc_tms_all_report'
    _description = 'Report TMS All'

    @api.model
    def _get_report_values(self, docids, data=None):
        
        docs = self.env['stock.picking'].browse(docids)

        keep_billing_status = []
        billing_ids = re.findall(r'\d+', data['billing_status'])
        billing_ids = [int(id_) for id_ in billing_ids]
        for billing in billing_ids:
            if billing:
                billing_status = self.env['billing.status.tms'].browse(billing)
                keep_billing_status.append(billing_status.code) # เปลี่ยนเป็น code

        keep_delivery_status = []
        delivery_ids = re.findall(r'\d+', data['delivery_status'])
        delivery_ids = [int(id_) for id_ in delivery_ids]
        for delivery in delivery_ids:
            if delivery:
                delivery_status = self.env['delivery.status.tms'].browse(delivery)
                keep_delivery_status.append(delivery_status.code) # เปลี่ยนเป็น code

        if data['keep_transport_line_code']:
            domain = [
                ('delivery_date', '>=', data['from_date']),
                ('delivery_date', '<=', data['to_date']),
                ('transport_desc', 'in', data['keep_transport_line_code'])
            ]
        else:
            domain = [
                ('delivery_date', '>=', data['from_date']),
                ('delivery_date', '<=', data['to_date']),
            ]

        if keep_billing_status:
            domain.append(('invoice_line_ids.billing_status', 'in', keep_billing_status)) # มาจาก invoice ในใบ delivery billing_status

        if keep_delivery_status:
            domain.append(('invoice_line_ids.delivery_status', 'in', keep_delivery_status)) # มาจาก invoice ในใบ delivery delivery_status

        distribution_deli_notes = self.env["distribition.delivery.note"].search(domain)

        sum_total_price = 0
        sum_count = 0

        from_date = fields.Date.from_string(data['from_date'])
        to_date = fields.Date.from_string(data['to_date'])
        if data['tms_remark']:
            distribution_deli_notes = distribution_deli_notes.filtered(lambda x: x.invoice_line_ids.filtered(lambda x: x.tms_remark == data['tms_remark']))

        for record in distribution_deli_notes:
            lines = record.invoice_line_ids
            if data['tms_remark']:
                lines = lines.filtered(lambda x: x.tms_remark == data['tms_remark'])
            sum_total_price += sum(line.amount_total for line in lines)
            sum_count += len(lines)

        str_from_date = from_date.strftime('%d-%m-%Y')
        str_to_date = to_date.strftime('%d-%m-%Y')

        report_values = {
            'from_date': str_from_date,
            'to_date': str_to_date,
            'distribution_deli_notes': distribution_deli_notes,
            'sum_total_price': sum_total_price,
            'sum_count': sum_count,
            'tms_remark': data['tms_remark']
        }
        return report_values