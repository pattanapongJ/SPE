# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

import io
import base64
import xlsxwriter

from odoo.tools import format_date
from datetime import datetime, timedelta
import calendar

# Define your wizard model
class WizardTmsMonth(models.TransientModel):
    _name = "wizard.tms.month"

    test = fields.Char(string="From")

    from_date = fields.Date(string="From", required=True)
    to_date = fields.Date(string="To", required=True)

    transport_desc_ids = fields.Many2many(
        "delivery.round",
        string="Transport Descriptions",
        relation="wizard_delivery_month",
        column1="wizard_id",
        column2="delivery_round_id",
    )

    driver_ids = fields.Many2many(
        "driver.model", 
        string="Driver", 
        relation="wizard_driver_month", 
        column1="wizard_id", 
        column2="driver_id"
    )

    delivery_status = fields.Many2many(
        "delivery.status.tms", 
        string="Delivery Status", 
        relation="wizard_deli_month", 
        column1="wizard_id", 
        column2="delivery_id"
    )

    billing_status = fields.Many2many(
        "billing.status.tms", 
        string="Billing Status", 
        relation="wizard_billing_month", 
        column1="wizard_id", 
        column2="billing_id"
    )
    tms_remark = fields.Char(
        string="TMS Remark",
    )

    def print_pdf(self):

        user_company = self.env.context['allowed_company_ids']
        all_company = self.env['res.company'].search([])

        if len(user_company) < len(all_company):
            raise UserError('Not Allow Please Change to Multi Companies')

        if self.from_date > self.to_date:
            raise UserError("Start Date Must Less Than End Date")

        if self.from_date > self.to_date:
            raise UserError("Start Date Must Less Than End Date")

        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'transport_desc_ids': self.transport_desc_ids,
            'driver_ids': self.driver_ids,
            'delivery_status': self.delivery_status,
            'billing_status': self.billing_status,
            'tms_remark': self.tms_remark
        }

        return self.env.ref('hdc_tms_general_report.tms_report_month_view').report_action(self, data=data)
    
    def print_excel(self):
        user_company = self.env.context['allowed_company_ids']
        all_company = self.env['res.company'].search([])

        if len(user_company) < len(all_company):
            raise UserError('Not Allow Please Change to Multi Companies')

        if self.from_date > self.to_date:
            raise UserError("Start Date Must Less Than End Date")

        if self.from_date > self.to_date:
            raise UserError("Start Date Must Be Less Than End Date")
                
        domain = [
            ('delivery_date', '>=', self.from_date),
            ('delivery_date', '<=', self.to_date)
        ]

        keep_transport_line_code = []
        keep_driver_line_name = []
        keep_delivery_status_name = []
        keep_billing_status_name = []

        if self.delivery_status:
            for delivery_status in self.delivery_status:
                keep_delivery_status_name.append(delivery_status.code)
            domain.append(('invoice_line_ids.delivery_status', 'in', keep_delivery_status_name))

        if self.billing_status:
            for billing_status in self.billing_status:
                keep_billing_status_name.append(billing_status.code)
            domain.append(('invoice_line_ids.billing_status', 'in', keep_billing_status_name))

        if self.transport_desc_ids:
            for trans_line in self.transport_desc_ids:
                keep_transport_line_code.append(trans_line.code)
            domain.append(('transport_desc', 'in', keep_transport_line_code))

        if self.driver_ids:
            for driver_id in self.driver_ids:
                keep_driver_line_name.append(driver_id.name)
            domain.append(('driver_id.name', 'in', keep_driver_line_name))

        if self.tms_remark:
            domain.append(('invoice_line_ids.tms_remark', '=', self.tms_remark))

        distribution_deli_notes = self.env["distribition.delivery.note"].search(domain)

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        str_from_date = self.from_date.strftime('%d-%m-%Y')
        str_to_date = self.to_date.strftime('%d-%m-%Y')


        worksheet.write(0, 0, 'รายงานจัดส่งสินค้าตามผู้จัดส่ง-แบบสรุป (รายเดือน)') # row, column, value
        worksheet.write(1, 0, str_from_date)
        worksheet.write(1, 1, 'ถึง')
        worksheet.write(1, 2, str_to_date)

        headers = ['ลำดับ', 'ชื่อผู้จัดส่ง', 'จำนวนบิล/ใบ']

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

        worksheet.write(2, 0, 'พิมพ์วันที่')
        worksheet.write(2, 1, formatted_date)
        worksheet.write(2, 2, 'เวลา')
        worksheet.write(2, 3, formatted_time)

        for col_num, header in enumerate(headers):
            worksheet.write(3, col_num, header)

        keep_driver = {}
        for line_deli in distribution_deli_notes:
            driver_name = line_deli.driver_id.name or ''
            invoice_line = line_deli.invoice_line_ids
            if self.tms_remark:
                keep_driver[driver_name] = keep_driver.get(driver_name, 0) + len(invoice_line.filtered(lambda x: x.tms_remark == self.tms_remark))
            else:
                keep_driver[driver_name] = keep_driver.get(driver_name, 0) + len(invoice_line)

        index = 1
        row_num = 4
        sum_count = 0
        for driver_name, count in keep_driver.items():
            worksheet.write(row_num, 0, index)
            worksheet.write(row_num, 1, driver_name)
            worksheet.write(row_num, 2, count)
            index += 1
            row_num += 1
            sum_count += count

        worksheet.write(row_num, 1, 'รวมทั้งสิ้น')
        worksheet.write(row_num, 2, sum_count)

        workbook.close()

        output.seek(0)
        excel_file_content = output.read()
        output.close()

        encoded_file = base64.b64encode(excel_file_content)

        attachment = self.env['ir.attachment'].create({
            'name': 'Transport_Report.xlsx',
            'type': 'binary',
            'datas': encoded_file,
            'store_fname': 'Transport_Report.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }