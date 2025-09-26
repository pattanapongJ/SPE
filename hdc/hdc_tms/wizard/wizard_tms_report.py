# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

import io
import base64
import xlsxwriter

# Define your wizard model
class WizardTmsReport(models.TransientModel):
    _name = "wizard.tms.report"

    test = fields.Char(string="From")

    from_date = fields.Date(string="From", required=True)
    to_date = fields.Date(string="To", required=True)

    transport_desc_ids = fields.Many2many(
        "delivery.round",
        string="Transport Descriptions",
        relation="wizard_tms_report_delivery_round_rel",
        column1="wizard_id",
        column2="delivery_round_id",
    )

    delivery_status = fields.Many2many(
        "delivery.status.tms", 
        string="Delivery Status", 
        relation="wizard_deli_tms", 
        column1="wizard_id", 
        column2="delivery_id"
    )

    billing_status = fields.Many2many(
        "billing.status.tms", 
        string="Billing Status", 
        relation="wizard_billing_tms", 
        column1="wizard_id", 
        column2="billing_id"
    )
    delivery_note_ids = fields.Many2many(
        "distribition.delivery.note", 
        string="Delivery Note", compute="_compute_delivery_note_ids"
    )
    tms_remark = fields.Char(
        string="TMS Remark", 
    )

    def _compute_delivery_note_ids(self):
        for record in self:
            if record.from_date and record.to_date:
                domain = [
                    ('tms_remark', '!=', False),
                    ('delivery_date', '>=', record.from_date),
                    ('delivery_date', '<=', record.to_date)
                ]
            
            elif record.from_date and not record.to_date:
                domain = [
                    ('tms_remark', '!=', False),
                    ('delivery_date', '>=', record.from_date)
                ]
            else:
                domain = [
                    ('tms_remark', '!=', False)
                ]
            record.delivery_note_ids = self.env['distribition.delivery.note'].search(domain)

    def print_pdf(self):

        user_company = self.env.context['allowed_company_ids']
        all_company = self.env['res.company'].search([])

        if len(user_company) < len(all_company):
            raise UserError('Not Allow Please Change to Multi Companies')

        if self.from_date > self.to_date:
            raise UserError("Start Date Must Less Than End Date")

        keep_transport_line_code = []

        for transport_desc in self.transport_desc_ids:
            keep_transport_line_code.append(transport_desc.code)

        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'keep_transport_line_code': keep_transport_line_code,
            'delivery_status': self.delivery_status,
            'billing_status': self.billing_status,
            'tms_remark': self.tms_remark
        }

        return self.env.ref('hdc_tms_general_report.tms_report_all_view').report_action(self, data=data)
    
    def print_excel(self):

        user_company = self.env.context['allowed_company_ids']
        all_company = self.env['res.company'].search([])

        if len(user_company) < len(all_company):
            raise UserError('Not Allow Please Change to Multi Companies')

        if self.from_date > self.to_date:
            raise UserError("Start Date Must Less Than End Date")
        
        if self.from_date > self.to_date:
            raise UserError("Start Date Must Be Less Than End Date")
        
        keep_transport_line_code = []
        keep_billing_status = []
        keep_delivery_status = []

        for transport_desc in self.transport_desc_ids:
            keep_transport_line_code.append(transport_desc.code)

        for bill in self.billing_status:
            keep_billing_status.append(bill.code)

        for deli in self.delivery_status:
            keep_delivery_status.append(deli.code)        

        
        domain = [
            ('delivery_date', '>=', self.from_date),
            ('delivery_date', '<=', self.to_date)
        ]

        if keep_transport_line_code:
            domain.append(('transport_desc', 'in', keep_transport_line_code))

        if keep_billing_status:
            domain.append(('invoice_line_ids.billing_status', 'in', keep_billing_status))

        if keep_delivery_status:
            domain.append(('invoice_line_ids.delivery_status', 'in', keep_delivery_status))

        distribution_deli_notes = self.env["distribition.delivery.note"].search(domain)

        sum_total_price = 0
        sum_count = 0
        if self.tms_remark:
            distribution_deli_notes = distribution_deli_notes.filtered(lambda x: x.invoice_line_ids.filtered(lambda x: x.tms_remark == self.tms_remark))

        for record in distribution_deli_notes:
            lines = record.invoice_line_ids
            if self.tms_remark:
                lines = lines.filtered(lambda x: x.tms_remark == self.tms_remark)
            sum_total_price += sum(line.amount_total for line in lines)            
            sum_count += len(lines)

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        str_from_date = self.from_date.strftime('%d-%m-%Y')
        str_to_date = self.to_date.strftime('%d-%m-%Y')


        worksheet.write(0, 0, 'รายงานจัดส่งสินค้าตามผู้จัดส่ง-แบบสรุป (รายวัน)')
        worksheet.write(1, 0, str_from_date)
        worksheet.write(1, 1, 'ถึง')
        worksheet.write(1, 2, str_to_date)

        headers = ['ลำดับ', 'ชื่อผู้จัดส่ง', 'จำนวนบิล/ใบ', 'ยอดเงิน', 'สายส่ง TRL']

        for col_num, header in enumerate(headers):
            worksheet.write(2, col_num, header)

        row_num = 3
        for index, doc in enumerate(distribution_deli_notes):
            worksheet.write(row_num, 0, index + 1)
            worksheet.write(row_num, 1, doc.driver_id.name)
            if self.tms_remark:
                worksheet.write(row_num, 2, len(doc.invoice_line_ids.filtered(lambda x: x.tms_remark == self.tms_remark)))
            else:
                worksheet.write(row_num, 2, len(doc.invoice_line_ids))
            if self.tms_remark:
                total_amount = sum(line.amount_total for line in doc.invoice_line_ids.filtered(lambda x: x.tms_remark == self.tms_remark))
            else:
                total_amount = sum(line.amount_total for line in doc.invoice_line_ids)
            worksheet.write(row_num, 3, total_amount)
            worksheet.write(row_num, 4, doc.transport_line_id.name)
            row_num += 1

        worksheet.write(row_num, 1, 'รวมทั้งสิ้น')
        worksheet.write(row_num, 2, sum_count)
        worksheet.write(row_num, 3, sum_total_price)

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

