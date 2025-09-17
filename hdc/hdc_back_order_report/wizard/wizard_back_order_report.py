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
class WizardBackOrderReport(models.TransientModel):
    _name = "wizard.back.order.report"

    from_date = fields.Date(string="From", required=True)
    to_date = fields.Date(string="To", required=True)

    back_order_by_type = fields.Selection([
        ('by_customer', 'ชื่อลูกค้า'),
        ('by_sale_person', 'Sale Response'),
        ('by_item', 'Item'),
        ('by_project', 'Project'),
    ], string="By Type", default="by_customer")

    partner_many_ids = fields.Many2many(
        "res.partner",
        string="Customer",
        relation="wizard_back_order_customer",
        column1="wizard_id",
        column2="partner_id",
    )
    # partner_id = fields.Many2one(comodel_name="res.partner", string="Customer")

    user_many_ids = fields.Many2many(
        "res.users",
        string="Salesperson",
        relation="wizard_back_order_saleperson",
        column1="wizard_id",
        column2="user_id",
    )
    # user_id = fields.Many2one(comodel_name="res.users", string="Salesperson")

    product_many_ids = fields.Many2many(
        "product.product",
        string="Product",
        relation="wizard_back_order_product",
        column1="wizard_id",
        column2="product_id",
    )
    # product_id = fields.Many2one('product.product', string='Product')

    project_many_names = fields.Many2many(
        "sale.project",
        string="Project Name",
        relation="wizard_back_order_project",
        column1="wizard_id",
        column2="project_name",
    )
    # project_name = fields.Many2one('sale.project', string='Project Name')

    def print_pdf(self):

        print('------print_pdf------')

        if self.from_date > self.to_date:
            raise UserError("Start Date Must Less Than End Date")        

        # Sale Respond ใช้ Sale อะไร???

        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'back_order_by_type': self.back_order_by_type,
            'partner_id': self.partner_many_ids,
            'user_id': self.user_many_ids,
            'product_id': self.product_many_ids,
            'project_name': self.project_many_names,
        }

        # print('------data------', data)

        if self.back_order_by_type == 'by_customer':
            return self.env.ref('hdc_back_order_report.back_order_customer_report').report_action(self, data=data)
        
        if self.back_order_by_type == 'by_sale_person':
            return self.env.ref('hdc_back_order_report.back_order_sale_response_report').report_action(self, data=data)
        
        if self.back_order_by_type == 'by_item':
            return self.env.ref('hdc_back_order_report.back_order_product_report').report_action(self, data=data)
        
        if self.back_order_by_type == 'by_project':
            return self.env.ref('hdc_back_order_report.back_order_project_report').report_action(self, data=data)
    
    def print_excel(self):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        head_cell_format_no_color = workbook.add_format({
            'bold': True, 'align': 'center', 'border': True, 'font_size': 9, 'font_name': 'Kanit', 'valign': 'vcenter'
        })

        datetime_format = workbook.add_format({'align': 'right'})
        datetime_format.set_font_size(9)
        datetime_format.set_align('vcenter')
        datetime_format.set_font_name('Kanit')
        
        border_format_buttom = workbook.add_format({'bold': True, 'bottom': 1})

        if self.from_date > self.to_date:
                raise UserError("Start Date Must Be Less Than End Date")
            
        domain = [
                ('last_date_delivered', '>=', self.from_date),
                ('last_date_delivered', '<=', self.to_date)
            ]
        
        if self.back_order_by_type == 'by_customer':
            
            worksheet.write(0, 0, 'SPE Back order lines by customer')

            current_dateTime = datetime.now() + timedelta(hours=7)
            worksheet.write(0, 8, current_dateTime.strftime('%d-%m-%y'),datetime_format)
            worksheet.write(1, 8, current_dateTime.strftime('%H:%M:%S'),datetime_format)
            
            worksheet.set_row(0, 20)
            worksheet.set_row(1, 15)
            worksheet.set_row(2, 15)

            worksheet.write(0, 3, 'Seng Charoen Group')

            row = 5

            def write_excel_headers(row):
                worksheet.set_row(row, 25)
                worksheet.write(row, 0, 'Ship date', head_cell_format_no_color)
                worksheet.write(row, 1, 'Sales order', head_cell_format_no_color)
                worksheet.write(row, 2, 'Item Number', head_cell_format_no_color)
                worksheet.write(row, 3, 'Item Name', head_cell_format_no_color)
                worksheet.write(row, 4, 'SO Status', head_cell_format_no_color)
                worksheet.write(row, 5, 'Line Status', head_cell_format_no_color)
                worksheet.write(row, 6, 'Remark', head_cell_format_no_color)
                worksheet.write(row, 7, 'Unit Price', head_cell_format_no_color)
                worksheet.write(row, 8, 'Discount', head_cell_format_no_color)
                worksheet.write(row, 9, 'Amount ordered', head_cell_format_no_color)
                worksheet.write(row, 10, 'Unit', head_cell_format_no_color)
                worksheet.write(row, 11, 'Quantity', head_cell_format_no_color)
                worksheet.write(row, 12, 'Delivery', head_cell_format_no_color)
                worksheet.write(row, 13, 'Delivery Remainder', head_cell_format_no_color)
                worksheet.write(row, 14, 'ค้างส่ง/ย่อย', head_cell_format_no_color)
                worksheet.write(row, 15, 'Invoice No.', head_cell_format_no_color)
                worksheet.write(row, 16, 'Spe Invoice No.', head_cell_format_no_color)
                worksheet.write(row, 17, 'Sales Spec', head_cell_format_no_color)
                worksheet.write(row, 18, 'Sales Responsible', head_cell_format_no_color)
                worksheet.write(row, 19, 'Sales Taker', head_cell_format_no_color)
                worksheet.write(row, 20, 'pool', head_cell_format_no_color)
                worksheet.write(row, 21, 'PO ลูกค้า', head_cell_format_no_color)
                worksheet.write(row, 22, 'โครงการ', head_cell_format_no_color)
                worksheet.write(row, 23, 'Picking Note', head_cell_format_no_color)
                worksheet.write(row, 24, 'Transfer ShipRemain', head_cell_format_no_color)
                worksheet.write(row, 25, 'Po สินค้าค้างรับ', head_cell_format_no_color)
                worksheet.write(row, 26, 'Delivery Date', head_cell_format_no_color)
                worksheet.write(row, 27, 'Onhand', head_cell_format_no_color)
                worksheet.write(row, 28, 'ค้าง Transfer', head_cell_format_no_color)
                worksheet.write(row, 29, 'แปลง/Type/block', head_cell_format_no_color)

            if self.partner_many_ids:
                customers = self.partner_many_ids
            else:
                sale_order_lines = self.env['sale.order.line'].search(domain)
                customers = set(line.order_id.partner_id for line in sale_order_lines)
            
            for customer in customers:
                worksheet.write(row, 0, 'Customer')
                row += 1
                worksheet.write_row(f'A{row}', [''] * 29, border_format_buttom)
                worksheet.write(row, 0, customer.ref if customer.ref else '')
                worksheet.write(row, 2, customer.name if customer.name else '')
                row += 1
                
                write_excel_headers(row)
                row += 1

                order_lines = self.env['sale.order.line'].search([('order_id.partner_id', '=', customer.id)] + domain)

                if order_lines:
                    for line in order_lines:
                        worksheet.write(row, 0, line.last_date_delivered.strftime('%d/%m/%Y'))
                        worksheet.write(row, 1, line.order_id.name if line.order_id.name else '')
                        worksheet.write(row, 2, line.product_id.default_code if line.product_id.default_code else '')
                        worksheet.write(row, 3, line.product_id.name if line.product_id.name else '')
                        worksheet.write(row, 4, 'Backorder')
                        worksheet.write(row, 5, 'Backorder')
                        worksheet.write(row, 6, line.note if line.note else '')
                        worksheet.write(row, 7, line.price_unit)
                        worksheet.write(row, 8, line.dis_price)
                        worksheet.write(row, 9, (line.price_unit * line.product_uom_qty) - line.dis_price)
                        worksheet.write(row, 10, line.product_uom.name if line.product_uom.name else '')
                        worksheet.write(row, 11, line.product_uom_qty)
                        worksheet.write(row, 12, line.qty_delivered)
                        worksheet.write(row, 13, line.product_uom_qty - line.qty_delivered)
                        worksheet.write(row, 14, '')

                        if line.order_id.invoice_ids:
                            keep_invoice_name = ''
                            keep_invoice_no = ''
                            for index, invoice_line in enumerate(line.order_id.invoice_ids):
                                if invoice_line.name:
                                    if index == 0:
                                        keep_invoice_name = str(invoice_line.name)
                                    else:
                                        keep_invoice_name += ', ' + str(invoice_line.name)
                                if invoice_line.form_no:
                                    if index == 0:
                                        keep_invoice_no = str(invoice_line.form_no)
                                    else:
                                        keep_invoice_no += ', ' + str(invoice_line.form_no)                                                                
                            worksheet.write(row, 15, keep_invoice_name)
                            worksheet.write(row, 16, keep_invoice_no)
                        else:
                            worksheet.write(row, 15, '')
                            worksheet.write(row, 16, '')

                        worksheet.write(row, 17, line.order_id.sale_spec.name if line.order_id.sale_spec else '')
                        worksheet.write(row, 18, line.order_id.user_id.name if line.order_id.user_id else '')
                        worksheet.write(row, 19, line.order_id.user_sale_agreement.name if line.order_id.user_sale_agreement else '')
                        worksheet.write(row, 20, '')
                        worksheet.write(row, 21, line.order_id.customer_po if line.order_id.customer_po else '')
                        worksheet.write(row, 22, line.order_id.project_name.project_name if line.order_id.project_name.project_name else '')
                        worksheet.write(row, 23, '')
                        worksheet.write(row, 24, '')

                        # Search Product in Picking List that state is in_progress and Operation Type is not Inter Transfer
                        product_picking = self.env['stock.picking.batch'].search([('move_tranfer_ids.product_id', '=', line.product_id.id), ('picking_type_id.code', '!=', 'internal')])                                    
                        total_product_picking = 0
                        if product_picking:
                            for picking_line in product_picking:
                                for move_tranfer_line in picking_line.move_tranfer_ids:
                                    if move_tranfer_line.product_id.id == line.product_id.id:
                                        total_product_picking += move_tranfer_line.product_uom_qty
                        worksheet.write(row, 25, total_product_picking)
                        
                        worksheet.write(row, 26, '')                            
                        worksheet.write(row, 27, line.product_id.qty_available)
                        worksheet.write(row, 28, '')
                        worksheet.write(row, 29, line.order_id.modify_type_txt if line.order_id.modify_type_txt else '')
                        row += 1
                    worksheet.write(row, 24, 'Test1')
                    worksheet.write(row, 25, 'Test2')
                    worksheet.write(row, 28, 'Test3')
                    row += 1                    

        if self.back_order_by_type == 'by_sale_person':
            
            worksheet.write(0, 0, 'SPE Back order lines by Sales Respond')

            current_dateTime = datetime.now() + timedelta(hours=7)
            worksheet.write(0, 8, current_dateTime.strftime('%d-%m-%y'),datetime_format)
            worksheet.write(1, 8, current_dateTime.strftime('%H:%M:%S'),datetime_format)
            
            worksheet.set_row(0, 20)
            worksheet.set_row(1, 15)
            worksheet.set_row(2, 15)

            worksheet.write(0, 3, 'Seng Charoen Group')

            row = 5

            def write_excel_headers(row):
                worksheet.set_row(row, 25)
                worksheet.write(row, 0, 'Ship date', head_cell_format_no_color)
                worksheet.write(row, 1, 'Cust Name', head_cell_format_no_color)
                worksheet.write(row, 2, 'Sales order', head_cell_format_no_color)
                worksheet.write(row, 3, 'Item Number', head_cell_format_no_color)
                worksheet.write(row, 4, 'Product Name', head_cell_format_no_color)
                worksheet.write(row, 5, 'Unit Price', head_cell_format_no_color)
                worksheet.write(row, 6, 'Discount', head_cell_format_no_color)
                worksheet.write(row, 7, 'Amount ordered', head_cell_format_no_color)
                worksheet.write(row, 8, 'Unit', head_cell_format_no_color)
                worksheet.write(row, 9, 'Quantity', head_cell_format_no_color)
                worksheet.write(row, 10, 'Delivery', head_cell_format_no_color)
                worksheet.write(row, 11, 'Delivery Remainder', head_cell_format_no_color)
                worksheet.write(row, 12, 'ค้างส่ง/ย่อย', head_cell_format_no_color)
                worksheet.write(row, 13, 'On order', head_cell_format_no_color)
                worksheet.write(row, 14, 'Invoice No', head_cell_format_no_color)
                worksheet.write(row, 15, 'Spe Invoice No', head_cell_format_no_color)
                worksheet.write(row, 16, 'Sales Spec', head_cell_format_no_color)
                worksheet.write(row, 17, 'PO ลูกค้า', head_cell_format_no_color)
                worksheet.write(row, 18, 'โครงการ', head_cell_format_no_color)
                worksheet.write(row, 19, 'แปลง/Type/block', head_cell_format_no_color)
                worksheet.write(row, 20, 'Transfer', head_cell_format_no_color)
                worksheet.write(row, 21, 'คลังอื่นๆ', head_cell_format_no_color)
                worksheet.write(row, 22, 'เสีย(NG)', head_cell_format_no_color)
                worksheet.write(row, 23, 'ซ่อม(RP)', head_cell_format_no_color)
                worksheet.write(row, 24, 'ฝากขาย(CG)', head_cell_format_no_color)
                worksheet.write(row, 25, 'ห้าง(MDT)', head_cell_format_no_color)
                worksheet.write(row, 26, '(MO)', head_cell_format_no_color)
                worksheet.write(row, 27, 'สินค้าค้างรับ', head_cell_format_no_color)
                worksheet.write(row, 28, 'Delivery Date', head_cell_format_no_color)
                worksheet.write(row, 29, 'Buyer Group', head_cell_format_no_color)
                worksheet.write(row, 30, 'ค้าง Transfer', head_cell_format_no_color)
                worksheet.write(row, 31, 'คลัง F1', head_cell_format_no_color)
                worksheet.write(row, 32, 'คลัง F2', head_cell_format_no_color)
                worksheet.write(row, 33, 'คลัง F6', head_cell_format_no_color)

            if self.user_many_ids:
                sale_persons = self.user_many_ids
            else:
                sale_order_lines = self.env['sale.order.line'].search(domain)
                sale_persons = set(line.order_id.user_id for line in sale_order_lines)

            for sale_person in sale_persons:
                worksheet.write(row, 0, 'Sales Resp')
                row += 1
                worksheet.write_row(f'A{row}', [''] * 33, border_format_buttom)
                worksheet.write(row, 0, sale_person.id if sale_person.id else '')
                worksheet.write(row, 2, sale_person.name if sale_person.name else '')
                row += 1

                write_excel_headers(row)
                row += 1

                order_lines = self.env['sale.order.line'].search([('order_id.user_id', '=', sale_person.id)] + domain)

                total_price_unit = 0
                total_dis_price = 0
                total_amount = 0
                total_qty = 0
                total_delivery = 0
                total_delivery_remaind = 0

                if order_lines:
                    for line in order_lines:
                        worksheet.write(row, 0, line.last_date_delivered.strftime('%d/%m/%Y'))
                        worksheet.write(row, 1, line.order_id.partner_id.name if line.order_id.partner_id.name else '')
                        worksheet.write(row, 2, line.order_id.name if line.order_id.name else '')
                        worksheet.write(row, 3, line.product_id.default_code if line.product_id.default_code else '')
                        worksheet.write(row, 4, line.product_id.name if line.product_id.name else '')
                        worksheet.write(row, 5, line.price_unit)
                        total_price_unit += line.price_unit
                        worksheet.write(row, 6, line.dis_price)
                        total_dis_price += line.dis_price
                        worksheet.write(row, 7, (line.price_unit * line.product_uom_qty) - line.dis_price)
                        total_amount += ((line.price_unit * line.product_uom_qty) - line.dis_price)
                        worksheet.write(row, 8, line.product_uom.name if line.product_uom.name else '')
                        worksheet.write(row, 9, line.product_uom_qty)
                        total_qty += line.product_uom_qty
                        worksheet.write(row, 10, line.qty_delivered)
                        total_delivery += line.qty_delivered
                        worksheet.write(row, 11, line.product_uom_qty - line.qty_delivered)
                        total_delivery_remaind += (line.product_uom_qty - line.qty_delivered)
                        worksheet.write(row, 12, '')
                        worksheet.write(row, 13, '')

                        if line.order_id.invoice_ids:
                            keep_invoice_name = ''
                            keep_invoice_no = ''
                            for index, invoice_line in enumerate(line.order_id.invoice_ids):
                                if invoice_line.name:
                                    if index == 0:
                                        keep_invoice_name = str(invoice_line.name)
                                    else:
                                        keep_invoice_name += ', ' + str(invoice_line.name)
                                if invoice_line.form_no:
                                    if index == 0:
                                        keep_invoice_no = str(invoice_line.form_no)
                                    else:
                                        keep_invoice_no += ', ' + str(invoice_line.form_no)                                                                
                            worksheet.write(row, 14, keep_invoice_name)
                            worksheet.write(row, 15, keep_invoice_no)
                        else:
                            worksheet.write(row, 14, '')
                            worksheet.write(row, 15, '')

                        worksheet.write(row, 16, line.order_id.sale_spec.name if line.order_id.sale_spec.name else '')
                        worksheet.write(row, 17, line.order_id.customer_po if line.order_id.customer_po else '')
                        worksheet.write(row, 18, line.order_id.project_name.project_name if line.order_id.project_name.project_name else '')
                        worksheet.write(row, 19, line.order_id.modify_type_txt if line.order_id.modify_type_txt else '')
                        worksheet.write(row, 20, '')
                        worksheet.write(row, 21, '')
                        worksheet.write(row, 22, '')
                        worksheet.write(row, 23, '')
                        worksheet.write(row, 24, '')
                        worksheet.write(row, 25, '')
                        worksheet.write(row, 26, '')
                        worksheet.write(row, 27, '')
                        worksheet.write(row, 28, '')
                        worksheet.write(row, 29, '')
                        worksheet.write(row, 30, '')
                        worksheet.write(row, 31, '')
                        worksheet.write(row, 32, '')
                        worksheet.write(row, 33, '')
                        row += 1
                    worksheet.write(row, 5, total_price_unit)
                    worksheet.write(row, 6, total_dis_price)
                    worksheet.write(row, 7, total_amount)
                    worksheet.write(row, 9, total_qty)
                    worksheet.write(row, 10, total_delivery)
                    worksheet.write(row, 11, total_delivery_remaind)
                    worksheet.write(row, 12, '')
                    worksheet.write(row, 19, '')
                    worksheet.write(row, 21, '')
                    worksheet.write(row, 22, '')
                    worksheet.write(row, 23, '')
                    worksheet.write(row, 24, '')
                    worksheet.write(row, 25, '')
                    worksheet.write(row, 26, '')
                    worksheet.write(row, 29, '')
                    worksheet.write(row, 30, '')
                    worksheet.write(row, 31, '')
                    worksheet.write(row, 32, '')
                    worksheet.write(row, 33, '')
                    row += 1    

        if self.back_order_by_type == 'by_item':

            worksheet.write(0, 0, 'SPE Back order lines by Item')

            current_dateTime = datetime.now() + timedelta(hours=7)
            worksheet.write(0, 8, current_dateTime.strftime('%d-%m-%y'),datetime_format)
            worksheet.write(1, 8, current_dateTime.strftime('%H:%M:%S'),datetime_format)
            
            worksheet.set_row(0, 20)
            worksheet.set_row(1, 15)
            worksheet.set_row(2, 15)

            worksheet.write(0, 3, 'Seng Charoen Group')

            row = 5

            def write_excel_headers(row):
                worksheet.set_row(row, 25)
                worksheet.write(row, 0, 'Ship date', head_cell_format_no_color)
                worksheet.write(row, 1, 'Customer', head_cell_format_no_color)
                worksheet.write(row, 2, 'Cust Name', head_cell_format_no_color)
                worksheet.write(row, 3, 'Custname Eng', head_cell_format_no_color)
                worksheet.write(row, 4, 'Sales order', head_cell_format_no_color)
                worksheet.write(row, 5, 'Po Date', head_cell_format_no_color)
                worksheet.write(row, 6, 'Req. Receipt Date', head_cell_format_no_color)
                worksheet.write(row, 7, 'Req. Ship Date', head_cell_format_no_color)
                worksheet.write(row, 8, 'Customer Req.', head_cell_format_no_color)
                worksheet.write(row, 9, 'Delivery Date', head_cell_format_no_color)
                worksheet.write(row, 10, 'So Status', head_cell_format_no_color)
                worksheet.write(row, 11, 'Doc. Status', head_cell_format_no_color)
                worksheet.write(row, 12, 'Line Status', head_cell_format_no_color)
                worksheet.write(row, 13, 'Unit', head_cell_format_no_color)
                worksheet.write(row, 14, 'Unit Price', head_cell_format_no_color)
                worksheet.write(row, 15, 'Discount', head_cell_format_no_color)
                worksheet.write(row, 16, 'Amount ordered', head_cell_format_no_color)
                worksheet.write(row, 17, 'Quantity', head_cell_format_no_color)
                worksheet.write(row, 18, 'Delivery', head_cell_format_no_color)
                worksheet.write(row, 19, 'Delivery remainder', head_cell_format_no_color)
                worksheet.write(row, 20, 'ค้างส่ง/ย่อย', head_cell_format_no_color)
                worksheet.write(row, 21, 'Invoice No', head_cell_format_no_color)
                worksheet.write(row, 22, 'Spe Invoice No.', head_cell_format_no_color)
                worksheet.write(row, 23, 'Sales Spec', head_cell_format_no_color)
                worksheet.write(row, 24, 'Sales Resp', head_cell_format_no_color)
                worksheet.write(row, 24, 'Sales Taker', head_cell_format_no_color)
                worksheet.write(row, 25, 'pool', head_cell_format_no_color)
                worksheet.write(row, 26, 'โครงการ', head_cell_format_no_color)
                worksheet.write(row, 27, 'แปลง/Type/block', head_cell_format_no_color)
                worksheet.write(row, 28, 'Po สินค้าค้างรับ', head_cell_format_no_color)
                worksheet.write(row, 29, 'Delivery Date', head_cell_format_no_color)
                worksheet.write(row, 30, 'WH Date', head_cell_format_no_color)
                worksheet.write(row, 31, 'On order', head_cell_format_no_color)
                worksheet.write(row, 32, 'Onhand', head_cell_format_no_color)
                worksheet.write(row, 33, 'Transfer ShipRemain', head_cell_format_no_color)
                worksheet.write(row, 34, 'Create Date', head_cell_format_no_color)


            
            if self.product_many_ids:
                product_lines = self.product_many_ids
            else:
                product_id_lines = self.env['sale.order.line'].search(domain)
                product_lines = set(line.product_id for line in product_id_lines)

            for product_line in product_lines:
                worksheet.write(row, 0, 'Item number')
                worksheet.write(row, 2, 'Item Name')
                row += 1
                worksheet.write_row(f'A{row}', [''] * 35, border_format_buttom)
                worksheet.write(row, 0, product_line.default_code if product_line.default_code else '')
                worksheet.write(row, 2, product_line.name if product_line.name else '')
                row += 1

                write_excel_headers(row)
                row += 1

                order_lines = self.env['sale.order.line'].search([('product_id', '=', product_line.id)] + domain)

                total_amount = 0
                total_qty = 0
                total_delivery = 0
                total_delivery_remaind = 0

                if order_lines:
                    for line in order_lines:
                        worksheet.write(row, 0, line.last_date_delivered.strftime('%d/%m/%Y'))
                        worksheet.write(row, 1, line.order_id.partner_id.ref if line.order_id.partner_id.ref else '')
                        worksheet.write(row, 2, line.order_id.partner_id.name if line.order_id.partner_id.name else '')
                        worksheet.write(row, 3, '')
                        worksheet.write(row, 4, line.order_id.name if line.order_id.name else '')
                        worksheet.write(row, 5, line.order_id.po_date if line.order_id.po_date else '')
                        worksheet.write(row, 6, '')
                        worksheet.write(row, 7, '')
                        worksheet.write(row, 8, '')
                        worksheet.write(row, 9, '')
                        worksheet.write(row, 10, 'Backorder')
                        worksheet.write(row, 11, '')
                        worksheet.write(row, 12, '')
                        worksheet.write(row, 13, line.product_uom.name if line.product_uom.name else '')
                        worksheet.write(row, 14, line.price_unit)
                        worksheet.write(row, 15, line.dis_price)
                        worksheet.write(row, 16, (line.price_unit * line.product_uom_qty) - line.dis_price)
                        total_amount += ((line.price_unit * line.product_uom_qty) - line.dis_price)
                        worksheet.write(row, 17, line.product_uom_qty)
                        total_qty += line.product_uom_qty
                        worksheet.write(row, 18, line.qty_delivered)
                        total_delivery += line.qty_delivered
                        worksheet.write(row, 19, line.product_uom_qty - line.qty_delivered)
                        total_delivery_remaind += (line.product_uom_qty - line.qty_delivered)
                        worksheet.write(row, 20, '')

                        if line.order_id.invoice_ids:
                            keep_invoice_name = ''
                            keep_invoice_no = ''
                            for index, invoice_line in enumerate(line.order_id.invoice_ids):
                                if invoice_line.name:
                                    if index == 0:
                                        keep_invoice_name = str(invoice_line.name)
                                    else:
                                        keep_invoice_name += ', ' + str(invoice_line.name)
                                if invoice_line.form_no:
                                    if index == 0:
                                        keep_invoice_no = str(invoice_line.form_no)
                                    else:
                                        keep_invoice_no += ', ' + str(invoice_line.form_no)                                                                
                            worksheet.write(row, 21, keep_invoice_name)
                            worksheet.write(row, 22, keep_invoice_no)
                        else:
                            worksheet.write(row, 21, '')
                            worksheet.write(row, 22, '')
                        
                        worksheet.write(row, 23, line.order_id.sale_spec.name if line.order_id.sale_spec.name else '')
                        worksheet.write(row, 24, line.order_id.user_id.name if line.order_id.user_id.name else '')
                        worksheet.write(row, 25, line.order_id.user_sale_agreement.name if line.order_id.user_sale_agreement.name else '')
                        worksheet.write(row, 26, line.order_id.project_name.project_name if line.order_id.project_name.project_name else '')
                        worksheet.write(row, 27, line.order_id.modify_type_txt if line.order_id.modify_type_txt else '')

                        # Search Product in Picking List that state is in_progress and Operation Type is not Inter Transfer
                        product_picking = self.env['stock.picking.batch'].search([('move_tranfer_ids.product_id', '=', line.product_id.id), ('picking_type_id.code', '!=', 'internal')])                                    
                        total_product_picking = 0
                        if product_picking:
                            for picking_line in product_picking:
                                for move_tranfer_line in picking_line.move_tranfer_ids:
                                    if move_tranfer_line.product_id.id == line.product_id.id:
                                        total_product_picking += move_tranfer_line.product_uom_qty
                        worksheet.write(row, 28, total_product_picking)

                        worksheet.write(row, 29, '')
                        worksheet.write(row, 30, '')
                        worksheet.write(row, 31, '')
                        worksheet.write(row, 32, line.product_id.qty_available)
                        worksheet.write(row, 33, '')
                        worksheet.write(row, 34, '')
                        row += 1
                    worksheet.write(row, 0, 'Total')
                    worksheet.write(row, 16, total_amount)
                    worksheet.write(row, 17, total_qty)
                    worksheet.write(row, 18, total_delivery)
                    worksheet.write(row, 19, total_delivery_remaind)
                    worksheet.write(row, 31, 'Total On order')
                    row += 1

            worksheet.write(row, 0, 'Grand total') #???

        if self.back_order_by_type == 'by_project':

            worksheet.write(0, 0, 'SPE Back order (Project)')

            current_dateTime = datetime.now() + timedelta(hours=7)
            worksheet.write(0, 8, current_dateTime.strftime('%d-%m-%y'),datetime_format)
            worksheet.write(1, 8, current_dateTime.strftime('%H:%M:%S'),datetime_format)
            
            worksheet.set_row(0, 20)
            worksheet.set_row(1, 15)
            worksheet.set_row(2, 15)

            worksheet.write(0, 3, 'Seng Charoen Group')

            row = 5

            def write_excel_headers1(row):
                # worksheet.set_row(row, 25)
                worksheet.write(row, 0, 'Sales order', head_cell_format_no_color)
                worksheet.write(row, 1, '', head_cell_format_no_color)
                worksheet.write(row, 2, 'PO ลูกค้า', head_cell_format_no_color)
                worksheet.write(row, 3, '', head_cell_format_no_color)
                worksheet.write(row, 4, 'Ship date', head_cell_format_no_color)
                worksheet.write(row, 5, 'Sales Responsible', head_cell_format_no_color)
                worksheet.write(row, 6, 'Sales Spec', head_cell_format_no_color)
                worksheet.write(row, 7, 'Sales Taker', head_cell_format_no_color)
                worksheet.write(row, 8, 'Sales โครงการ', head_cell_format_no_color)
                worksheet.write(row, 9, '', head_cell_format_no_color)
                worksheet.write(row, 10, '', head_cell_format_no_color)
                worksheet.write(row, 11, '', head_cell_format_no_color)
                worksheet.write(row, 12, '', head_cell_format_no_color)
                worksheet.write(row, 13, '', head_cell_format_no_color)
                worksheet.write(row, 14, 'แปลง/type/Block', head_cell_format_no_color)
                worksheet.write(row, 15, '', head_cell_format_no_color)
                worksheet.write(row, 16, '', head_cell_format_no_color)
                worksheet.write(row, 17, '', head_cell_format_no_color)

            def write_excel_headers2(row):
                worksheet.write(row, 0, '', head_cell_format_no_color)
                worksheet.write(row, 1, 'Item number', head_cell_format_no_color)
                worksheet.write(row, 2, '', head_cell_format_no_color)
                worksheet.write(row, 3, 'Item Name', head_cell_format_no_color)
                worksheet.write(row, 4, '', head_cell_format_no_color)
                worksheet.write(row, 5, '', head_cell_format_no_color)
                worksheet.write(row, 6, '', head_cell_format_no_color)
                worksheet.write(row, 7, '', head_cell_format_no_color)
                worksheet.write(row, 8, '', head_cell_format_no_color)
                worksheet.write(row, 9, 'Quantity', head_cell_format_no_color)
                worksheet.write(row, 10, 'Delivery', head_cell_format_no_color)
                worksheet.write(row, 11, 'Delivery Remain', head_cell_format_no_color)
                worksheet.write(row, 12, 'Po ค้างรับ', head_cell_format_no_color)
                worksheet.write(row, 13, 'Amount', head_cell_format_no_color)
                worksheet.write(row, 14, 'WH Date', head_cell_format_no_color)
                worksheet.write(row, 15, 'On order', head_cell_format_no_color)
                worksheet.write(row, 16, 'Onhand', head_cell_format_no_color)
                worksheet.write(row, 17, 'Transfer ShipRemain', head_cell_format_no_color)

            if self.project_many_names:
                project_lines = self.project_many_names
            else:
                project_id_lines = self.env['sale.order.line'].search(domain)
                project_lines = set(line.order_id.project_name for line in project_id_lines)
            
            for project_line in project_lines:
                worksheet.write(row, 0, 'Customer')
                row += 1
                worksheet.write_row(f'A{row}', [''] * 18, border_format_buttom)
                worksheet.write(row, 0, project_line.code if project_line.code else '')
                worksheet.write(row, 2, project_line.project_name if project_line.project_name else '')
                row += 1
                
                write_excel_headers1(row)
                row += 1

                write_excel_headers2(row)
                row += 1

                order_lines = self.env['sale.order.line'].search([('order_id.project_name', '=', project_line.id)] + domain)

                written_order_ids = set()

                if order_lines:
                    for line in order_lines:
                        if line.order_id.name not in written_order_ids:
                            worksheet.write(row, 0, line.order_id.name if line.order_id.name else '')
                            worksheet.write(row, 2, line.order_id.customer_po if line.order_id.customer_po else '')
                            worksheet.write(row, 4, line.last_date_delivered.strftime('%d/%m/%Y'))
                            worksheet.write(row, 5, line.order_id.user_id.name if line.order_id.user_id.name else '')
                            worksheet.write(row, 6, line.order_id.sale_spec.name if line.order_id.sale_spec else '')
                            worksheet.write(row, 7, line.order_id.user_sale_agreement.name if line.order_id.user_sale_agreement.name else '')
                            worksheet.write(row, 8, line.order_id.project_name.project_name if line.order_id.project_name.project_name else '')
                            worksheet.write(row, 14, '')

                            written_order_ids.add(line.order_id.name if line.order_id.name else '')

                            row += 1

                            # Loop For Product in SO

                            so_line = self.env['sale.order.line'].search([('order_id.name', '=', line.order_id.name)])

                            total_amount = 0

                            if so_line:
                                for line_line in so_line:
                                    worksheet.write(row, 1, line_line.product_id.default_code if line_line.product_id.default_code else '')
                                    worksheet.write(row, 3, line_line.product_id.name if line_line.product_id.name else '')
                                    worksheet.write(row, 9, line_line.product_uom_qty)
                                    worksheet.write(row, 10, line_line.qty_delivered)
                                    worksheet.write(row, 11, line_line.product_uom_qty - line_line.qty_delivered)

                                    # Search Product in Picking List that state is in_progress and Operation Type is not Inter Transfer
                                    product_picking = self.env['stock.picking.batch'].search([('move_tranfer_ids.product_id', '=', line_line.product_id.id), ('picking_type_id.code', '!=', 'internal')])                                    
                                    total_product_picking = 0
                                    if product_picking:
                                        for picking_line in product_picking:
                                            for move_tranfer_line in picking_line.move_tranfer_ids:
                                                if move_tranfer_line.product_id.id == line_line.product_id.id:
                                                    total_product_picking += move_tranfer_line.product_uom_qty
                                    worksheet.write(row, 12, total_product_picking)

                                    worksheet.write(row, 13, '')
                                    worksheet.write(row, 14, line_line.order_id.modify_type_txt if line_line.order_id.modify_type_txt else '')
                                    worksheet.write(row, 15, '')
                                    worksheet.write(row, 16, line_line.product_id.qty_available)
                                    worksheet.write(row, 17, '')
                                    row += 1
                                worksheet.write(row, 12, 'Total')
                                worksheet.write(row, 13, '')
                                row += 1
                                worksheet.write(row, 12, 'Grand Total')
                                worksheet.write(row, 13, '')
                                row += 1                  

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