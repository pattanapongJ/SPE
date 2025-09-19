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
class WizardTmsEnumerate(models.TransientModel):
    _name = "wizard.tms.enumerate"

    test = fields.Char(string="From")

    from_date = fields.Date(string="From", required=True)
    to_date = fields.Date(string="To", required=True)

    transport_desc_ids = fields.Many2many(
        "delivery.round",
        string="Transport Descriptions",
        relation="wizard_delivery_enumerate",
        column1="wizard_id",
        column2="delivery_round_id",
    )

    driver_ids = fields.Many2many(
        "driver.model", 
        string="Driver", 
        relation="wizard_driver_enumerate", 
        column1="wizard_id", 
        column2="driver_id"
    )

    delivery_status_non = fields.Many2many(
        "delivery.status", 
        string="Delivery Status", 
        relation="wizard_deli_enumerate", 
        column1="wizard_id", 
        column2="delivery_id"
    )

    billing_status_non = fields.Many2many(
        "billing.status", 
        string="Billing Status", 
        relation="wizard_billing_enumerate", 
        column1="wizard_id", 
        column2="billing_id"
    )

    delivery_status = fields.Many2many(
        "delivery.status.tms", 
        string="Delivery Status", 
        relation="wizard_deli_enumerate_new", 
        column1="wizard_id", 
        column2="delivery_id"
    )

    billing_status = fields.Many2many(
        "billing.status.tms", 
        string="Billing Status", 
        relation="wizard_billing_enumerate_new", 
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

        return self.env.ref('hdc_tms_general_report.tms_report_enumerate_view').report_action(self, data=data)
    
    def print_excel(self):
        print('------print_excel------')

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


        worksheet.write(0, 0, 'รายงานการจัดส่งสินค้าตามผู้จัดส่ง-แบบแจกแจง') # row, column, value
        worksheet.write(1, 0, str_from_date)
        worksheet.write(1, 1, 'ถึง')
        worksheet.write(1, 2, str_to_date)

        headers = ['ลำดับ', 'วันที่เอกสาร', 'เลขที่เอกสาร', 'ชื่อลูกค้า', 'สายส่งTRL', 'Invoice Id', 'SPE Invoice', 'Document Date', 'จำนวนเงิน', 'Payment', 'หมายเหตุ', 'ผู้จัดทำ', 'ผู้จัดส่ง']

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

        row_num = 4
        sum_count = 0
        sum_total = 0
        num_deli = 0
        for line_deli_note in distribution_deli_notes:
            for index, doc in enumerate(line_deli_note.invoice_line_ids):
                if index == 0:
                    num_deli += 1
                    worksheet.write(row_num, 0, num_deli)
                    worksheet.write(row_num, 11, line_deli_note.user_id.name)
                    if line_deli_note.driver_id.name:
                        worksheet.write(row_num, 12, line_deli_note.driver_id.name)

                delivery_date_str = doc.distribition_id.delivery_date.strftime('%d/%m/%Y')
                worksheet.write(row_num, 1, delivery_date_str)

                worksheet.write(row_num, 2, line_deli_note.name)
                worksheet.write(row_num, 3, doc.partner_id.name)
                worksheet.write(row_num, 4, doc.transport_line_id.code)
                worksheet.write(row_num, 5, doc.invoice_id.name)

                if doc.spe_invoice:
                    worksheet.write(row_num, 6, doc.spe_invoice)

                invoice_date_str = doc.invoice_date.strftime('%d/%m/%Y')
                worksheet.write(row_num, 7, invoice_date_str)

                worksheet.write(row_num, 8, doc.amount_total)
                if doc.finance_type:
                    worksheet.write(row_num, 9, doc.finance_type)
                if doc.remark:
                    worksheet.write(row_num, 10, doc.remark)
                row_num += 1

            if self.tms_remark:
                total_amount = sum(line.amount_total for line in line_deli_note.invoice_line_ids.filtered(lambda x: x.tms_remark == self.tms_remark))
            else:
                total_amount = sum(line.amount_total for line in line_deli_note.invoice_line_ids)                
            if self.tms_remark:
                sum_count += len(line_deli_note.invoice_line_ids.filtered(lambda x: x.tms_remark == self.tms_remark))
            else:
                sum_count += len(line_deli_note.invoice_line_ids)
            sum_total += total_amount

        worksheet.write(row_num, 1, 'รวมทั้งสิ้น')
        worksheet.write(row_num, 2, sum_count)
        worksheet.write(row_num, 8, sum_total)

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