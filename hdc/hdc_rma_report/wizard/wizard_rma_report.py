from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

import io
import base64
import xlsxwriter
import io
from PIL import Image
from odoo import models


class RmaReport(models.TransientModel):
    _name = "wizard.rma.report"
    _description = "Wizard Create RMA Report"

    # name = fields.Char(string="Test")

    start_date = fields.Date(string="From", required=True)
    end_date = fields.Date(string="To", required=True)
    job_no_ids = fields.Many2many("crm.claim.ept",string="Job No.",relation="wizard_rma_job_no",column1="wizard_job_no_id",column2="rma_job_no_id")
    
    product_ids = fields.Many2many("product.product",string="Material",relation="wizard_rma_material_id",column1="wizard_material_id",column2="rma_material_id")

    company_id = fields.Many2one("res.company", string = "Company", default=lambda self: self.env.company)


    out_of_warranty = fields.Boolean()
    under_warranty = fields.Boolean()
    is_dewalt = fields.Boolean()

    def print_pdf(self):
        if self.start_date > self.end_date:
            raise UserError("Start Date Must Less Than End Date")
        
        keep_job_no_ids = []

        for job_no in self.job_no_ids:
            keep_job_no_ids.append(job_no.is_job_no)
        
        keep_product_ids = []

        for product_id in self.product_ids:
            keep_product_ids.append(product_id.id)

        data = {
            'is_dewalt': self.is_dewalt,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'keep_job_no_ids': keep_job_no_ids,
            'out_of_warranty': self.out_of_warranty,
            'under_warranty': self.under_warranty,
            'keep_product_ids': keep_product_ids
        }

        return self.env.ref('hdc_rma_report.rma_report_view').report_action(self, data=data)

    def print_excel(self):

        if self.start_date > self.end_date:
            raise UserError("Start Date Must Less Than End Date")

        keep_job_no_ids = []

        for job_no in self.job_no_ids:
            keep_job_no_ids.append(job_no.is_job_no)

        list_product_id_selected = []

        for product_id in self.product_ids:
            list_product_id_selected.append(product_id.id)

        if len(keep_job_no_ids) > 0:
            domain = [
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('is_job_no', 'in', keep_job_no_ids)
            ]
        else:
            domain = [
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date)
            ]

        if self.is_dewalt:
            domain.append(('is_dewalt', '=', True))
            if self.out_of_warranty and self.under_warranty:
                domain.append(('warranty_type', 'in', ['out', 'under']))
            elif self.out_of_warranty:
                domain.append(('warranty_type', '=', 'out'))
            elif self.under_warranty:
                domain.append(('warranty_type', '=', 'under'))


        record_RMA_filter = self.env['crm.claim.ept'].search(domain)

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        image_company = self.company_id.logo
        if image_company:
            image = io.BytesIO(base64.b64decode(image_company))
        else:
            image = False

        if image:
            worksheet.set_row(0, 80)
            product_image = image
            imageTosize = Image.open(product_image)
            newsizeImage = imageTosize.resize((80, 80), Image.ANTIALIAS)
            img_output = io.BytesIO()
            newsizeImage.save(img_output, format=imageTosize.format, optimize=True, quality=True)
            worksheet.insert_image(0 ,0 ,'image' , {
                'image_data': img_output,
                'x_scale': 1,
                'y_scale': 1,
                'x_offset': 20, 
                'y_offset': 5
            })
        # worksheet.merge_range(0, 2, 0, 7, "")
        # worksheet.merge_range(0, 8, 0, 13, "")

        name_th = self.company_id.name_th or ""
        name = self.company_id.name or ""
        phone_th = self.company_id.phone_th or ""
        fax_th = self.company_id.fax_th or ""
        street_th = self.company_id.street_th or ""
        street2_th = self.company_id.street2_th or ""
        street = self.company_id.street or ""
        street2 = self.company_id.street2 or ""

        worksheet.write(0, 2, name_th + '\n' + name + '\n' + phone_th + '\n' + fax_th)
        
        worksheet.write(0, 3, street_th + '\n' + street2_th + '\n' + street + '\n' + street2)

        headers = [
            'No.', 'Create on', 'Reference', 'Material', 
            'Material Description', 'Qty', 'Net Value/THB'
        ]

        for col_num, header in enumerate(headers):
            worksheet.write(1, col_num, header)

        row_num = 2
        
        if len(list_product_id_selected) > 0:
            index_count = 0
            for index, doc in enumerate(record_RMA_filter):
                dup_no = 0
                for line in doc.claim_line_ids:
                    if line.product_id.id in list_product_id_selected:
                        if not dup_no > 0:
                            worksheet.write(row_num, 0, index_count + 1)
                            index_count += 1
                        else:
                            worksheet.write(row_num, 0, '')
                        date_str = doc.date.strftime('%d-%m-%Y')
                        worksheet.write(row_num, 1, date_str)
                        is_job_no = doc.is_job_no or ""
                        account_id_name = doc.account_id.name or ""
                        worksheet.write(row_num, 2, is_job_no + '/' +account_id_name)
                        worksheet.write(row_num, 3, line.product_id.default_code)
                        worksheet.write(row_num, 4, line.product_id.name)
                        worksheet.write(row_num, 5, line.done_qty)
                        worksheet.write(row_num, 6, line.product_id.lst_price)
                        row_num += 1
                        dup_no += 1
        
                for line in doc.crm_claim_ept_line_ids:
                    worksheet.write(row_num, 0, '')
                    date_str = doc.date.strftime('%d-%m-%Y')
                    worksheet.write(row_num, 1, date_str)
                    is_job_no = doc.is_job_no or ""
                    account_id_name = doc.account_id.name or ""
                    worksheet.write(row_num, 2, is_job_no + '/' +account_id_name)
                    worksheet.write(row_num, 3, line.line_description)
                    worksheet.write(row_num, 4, line.line_product_id.name)
                    worksheet.write(row_num, 5, line.line_qty)
                    worksheet.write(row_num, 6, line.line_subtotal)
                    row_num += 1
        
        else:
            index_count = 0
            for index, doc in enumerate(record_RMA_filter):
                dup_no = 0
                for line in doc.claim_line_ids:
                    if not dup_no > 0:
                        worksheet.write(row_num, 0, index_count + 1)
                        index_count += 1
                    else:
                        worksheet.write(row_num, 0, '')
                    date_str = doc.date.strftime('%d-%m-%Y')
                    worksheet.write(row_num, 1, date_str)
                    is_job_no = doc.is_job_no or ""
                    account_id_name = doc.account_id.name or ""
                    worksheet.write(row_num, 2, is_job_no + '/' +account_id_name)
                    worksheet.write(row_num, 3, line.product_id.default_code)
                    worksheet.write(row_num, 4, line.product_id.name)
                    worksheet.write(row_num, 5, line.done_qty)
                    worksheet.write(row_num, 6, line.product_id.lst_price)
                    row_num += 1
                    dup_no += 1
                
                for line in doc.crm_claim_ept_line_ids:
                    worksheet.write(row_num, 0, '')
                    date_str = doc.date.strftime('%d-%m-%Y')
                    worksheet.write(row_num, 1, date_str)
                    is_job_no = doc.is_job_no or ""
                    account_id_name = doc.account_id.name or ""
                    worksheet.write(row_num, 2, is_job_no + '/' +account_id_name)
                    worksheet.write(row_num, 3, line.line_description)
                    worksheet.write(row_num, 4, line.line_product_id.name)
                    worksheet.write(row_num, 5, line.line_qty)
                    worksheet.write(row_num, 6, line.line_subtotal)
                    row_num += 1

        workbook.close()

        output.seek(0)
        excel_file_content = output.read()
        output.close()

        encoded_file = base64.b64encode(excel_file_content)
        
        attachment = self.env['ir.attachment'].create({
            'name': 'RMA_Report.xlsx',
            'type': 'binary',
            'datas': encoded_file,
            'store_fname': 'RMA_Report.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }
        