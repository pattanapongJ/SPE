# -*- coding: utf-8 -*-
import base64
import io
from odoo import models, fields, api
from collections import defaultdict
from datetime import datetime, time

class ReportSaleExcel(models.AbstractModel):
    _name = 'report.hdc_sale_report.sale_reporting'
    _description = 'Sale Reporting'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        format_detail_center = workbook.add_format({'align': 'center','bold': True, 'border': True, 'size': 14})
        format_detail = workbook.add_format({'align': 'left', 'border': True, 'size': 14})
        format_number = workbook.add_format({'align': 'right', 'border': True, 'size': 14})
        format_footerC_bold2 = workbook.add_format({'align': 'center', 'bold': True, 'top': True, 'left': True, 'right': True, 'size': 14})
        format_header = workbook.add_format({'align': 'center','border': True,'bold': True,'size': 14})
        format_detail_center.set_font_name('AngsanaUPC')
        format_header.set_text_wrap()
        format_detail.set_font_name('AngsanaUPC')
        format_number.set_font_name('AngsanaUPC')
        format_header.set_font_name('AngsanaUPC')
        format_footerC_bold2.set_font_name('AngsanaUPC')
        if data['document_type'] == 'sale':
            sheet = workbook.add_worksheet('รายงานจัดลําดับยอดขายตามพนักงาน')
        elif data['document_type'] == 'category':
            sheet = workbook.add_worksheet('รายงานยอดขายสินค้าตามประเภทสินค้า')
        elif data['document_type'] == 'brand':
            sheet = workbook.add_worksheet('รายงานจัดลำดับยอดขายตามยี่ห้อ')
        elif data['document_type'] == 'customer':
            sheet = workbook.add_worksheet('รายงานจัดลําดับยอดขายตามลูกค้า')
        company_id = self.env.company
        sheet.merge_range('A1:H1', company_id.name_th, format_footerC_bold2)
        
        sheet.set_column('A:A', 8)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 10)

        day_to = ''
        text_month_to = ''
        year_to = ''
        day_from = ''
        text_month_from = ''
        year_from = ''

        date_from = data['start_date']
        if date_from:
            day_from = str(date_from).split('-')[2]
            month_from = str(date_from).split('-')[1]
            year_from = str(date_from).split('-')[0]
            if year_from:
                year_from = int(year_from) + 543

        date_to = data['end_date']

        if date_to:
            day_to = str(date_to).split('-')[2]
            month_to = str(date_to).split('-')[1]
            year_to = str(date_to).split('-')[0]
            if year_to:
                year_to = int(year_to) + 543

        title_date = 'ระหว่างวันที่ '+ str(day_from) + '/' + str(month_from) + '/' + str(year_from) + ' ถึง ' + str(day_to) + '/' + str(month_to) + '/' + str(year_to)
        sheet.merge_range('A3:H3', title_date, format_footerC_bold2)
        
        filter_option = []
        # แปลง start_date จาก string เป็น datetime.date
        start_date = datetime.strptime(data['start_date'], "%Y-%m-%d").date()

        # แปลง end_date จาก string เป็น datetime.date
        end_date = datetime.strptime(data['end_date'], "%Y-%m-%d").date()

        # สร้างวันที่เริ่มต้นของวันที่เลือก (00:00:00)
        start_datetime = datetime.combine(start_date, time.min)

        # สร้างวันที่สิ้นสุดของวันที่เลือก (23:59:59)
        end_datetime = datetime.combine(end_date, time.max)
        
        filter_option += [('date_order','>=',start_datetime)]
        filter_option += [('date_order','<=',end_datetime)]

        if data['document_type'] == 'sale':
            sheet.merge_range('A2:H2', "รายงานจัดลําดับยอดขายตามพนักงาน", format_footerC_bold2)
            if data['saleman_id']:
                filter_option += [('user_id','in',data['saleman_id'])]
            if data['saleteam_id']:
                filter_option += [('team_id','in',data['saleteam_id'])]

            
            row = 3 
            col = 0
            sheet.write(3, 0, 'ลำดับที่', format_header)
            sheet.write(3, 1, 'ชื่อพนักงาน', format_header)
            sheet.write(3, 2, 'จำนวนขายสุทธิ', format_header)
            sheet.write(3, 3, 'จำนวนแถม', format_header)
            sheet.write(3, 4, 'ยอดขายสุทธิ', format_header)
            sheet.write(3, 5, 'ต้นทุน', format_header)
            sheet.write(3, 6, 'กำไร (บาท)', format_header)
            sheet.write(3, 7, 'กำไร%', format_header)

            sales_orders = self.env['sale.order'].search(filter_option)

            sales_data = {}
            for order in sales_orders:
                sale_person_name = order.user_id.name
                if sale_person_name not in sales_data:
                    sales_data[sale_person_name] = {
                        'total_sales_quantity': 0,
                        'total_free_product_qty': 0,
                        'total_sales_amount': 0,
                        'total_cost': 0,
                        'total_profit': 0,
                    }
                for line in order.order_line:
                    if line.product_id.free_product:
                        sales_data[sale_person_name]['total_free_product_qty'] += line.product_uom_qty

                sales_data[sale_person_name]['total_sales_quantity'] += sum(order.order_line.mapped('product_uom_qty'))
                sales_data[sale_person_name]['total_sales_amount'] += order.amount_untaxed
                sales_data[sale_person_name]['total_cost'] += sum(order.order_line.mapped(lambda line: line.product_id.standard_price * line.product_uom_qty))
                sales_data[sale_person_name]['total_profit'] += sum(order.order_line.mapped(lambda line: line.price_subtotal - (line.product_id.standard_price * line.product_uom_qty)))

            no_count = 0
            sum_profit = 0
            sum_total_sales_amount = 0
            sum_total_cost = 0
            for sale_person_name, data in sales_data.items():
                no_count += 1
                sum_total_sales_amount += data['total_sales_amount']
                sum_total_cost += data['total_cost']

                row += 1
                sheet.write(row, 0, no_count, format_detail)
                sheet.write(row, 1, sale_person_name, format_detail)
                sheet.write(row, 2, '{:.2f}'.format(round(data['total_sales_quantity'], 2)), format_number)
                sheet.write(row, 3, '{:.2f}'.format(round(data['total_free_product_qty'], 2)), format_number)
                sheet.write(row, 4, '{:.2f}'.format(round(data['total_sales_amount'], 2)), format_number)
                sheet.write(row, 5, '{:.2f}'.format(round(data['total_cost'], 2)), format_number)
                sheet.write(row, 6, '{:.2f}'.format(round(data['total_profit'], 2)), format_number)
                if data['total_sales_amount'] == 0:
                    formatted_value = "0.00"
                else:
                    formatted_value = '{:.2f}'.format(round((data['total_profit'] / data['total_sales_amount']) * 100, 2))
                sheet.write(row, 7, formatted_value, format_number)


            row += 1
            sum_profit = sum_total_sales_amount - sum_total_cost
            if sum_total_sales_amount == 0:
                sum_formatted_value = "0.00"
            else:
                sum_formatted_value = '{:.2f}'.format(round((sum_profit/sum_total_sales_amount)*100, 2))

            sheet.merge_range(row, 0,row,3, "รวมทั้งหมด", format_detail_center)
            sheet.write(row, 4, '{:.2f}'.format(round(sum_total_sales_amount, 2)), format_number)
            sheet.write(row, 5, '{:.2f}'.format(round(sum_total_cost, 2)), format_number)
            sheet.write(row, 6, '{:.2f}'.format(round(sum_profit, 2)), format_number)
            sheet.write(row, 7, sum_formatted_value, format_number)

        elif data['document_type'] == 'category':
            sheet.merge_range('A2:H2', "รายงานยอดขายสินค้าตามประเภทสินค้า", format_footerC_bold2)
            domain = [('active','=',True)]
            if data['categories']:
                domain += [('categ_id','in',data['categories'])]

            sale_detail_all = self.env['sale.order'].search(filter_option)
            product_filter_categories = self.env['product.template'].search(domain)
            order_detail = self.env['sale.order.line'].search([("order_id","in",sale_detail_all.ids),("product_template_id","in",product_filter_categories.ids)])

            categ_id_data = {}
            for order in order_detail:
                categ_id = order.product_id.categ_id
                if categ_id not in categ_id_data:
                    categ_id_data[categ_id] = {
                        'total_categ_id_quantity': 0,
                        'total_free_product_qty': 0,
                        'total_categ_id_amount': 0,
                        'total_cost': 0,
                        'total_profit': 0,
                    }
                if order.product_id.free_product:
                    categ_id_data[categ_id]['total_free_product_qty'] += order.product_uom_qty

                categ_id_data[categ_id]['total_categ_id_quantity'] += order.product_uom_qty
                categ_id_data[categ_id]['total_categ_id_amount'] += (order.price_unit * order.product_uom_qty)
                categ_id_data[categ_id]['total_cost'] += (order.product_id.standard_price * order.product_uom_qty)
                categ_id_data[categ_id]['total_profit'] += (order.price_unit * order.product_uom_qty) - (order.product_id.standard_price * order.product_uom_qty)
            
            row = 3 
            sheet.write(3, 0, 'ลำดับที่', format_header)
            sheet.write(3, 1, 'ประเภทสินค้า', format_header)
            sheet.write(3, 2, 'จำนวนขายสุทธิ', format_header)
            sheet.write(3, 3, 'จำนวนแถม', format_header)
            sheet.write(3, 4, 'ยอดขายสุทธิ', format_header)
            sheet.write(3, 5, 'ต้นทุน', format_header)
            sheet.write(3, 6, 'กำไร (บาท)', format_header)
            sheet.write(3, 7, 'กำไร%', format_header)

            no_count = 0
            sum_profit = 0
            sum_total_amount = 0
            sum_total_cost = 0
            for categ_id, data in categ_id_data.items():
                no_count += 1
                sum_total_amount += data['total_categ_id_amount']
                sum_total_cost += data['total_cost']
                row += 1
                sheet.write(row, 0, no_count, format_detail)
                sheet.write(row, 1, categ_id.name, format_detail)
                sheet.write(row, 2, '{:.2f}'.format(round(data['total_categ_id_quantity'], 2)), format_number)
                sheet.write(row, 3, '{:.2f}'.format(round(data['total_free_product_qty'], 2)), format_number)
                sheet.write(row, 4, '{:.2f}'.format(round(data['total_categ_id_amount'], 2)), format_number)
                sheet.write(row, 5, '{:.2f}'.format(round(data['total_cost'], 2)), format_number)
                sheet.write(row, 6, '{:.2f}'.format(round(data['total_profit'], 2)), format_number)
                if data['total_categ_id_amount'] == 0:
                    formatted_value = "0.00"
                else:
                    formatted_value = '{:.2f}'.format(round((data['total_profit'] / data['total_categ_id_amount']) * 100, 2))
                sheet.write(row, 7, formatted_value, format_number)


            row += 1
            sum_profit = sum_total_amount - sum_total_cost
            if sum_total_amount == 0:
                sum_formatted_value = "0.00"
            else:
                sum_formatted_value = '{:.2f}'.format(round((sum_profit/sum_total_amount)*100, 2))

            sheet.merge_range(row, 0,row,3, "รวมทั้งหมด", format_detail_center)
            sheet.write(row, 4, '{:.2f}'.format(round(sum_total_amount, 2)), format_number)
            sheet.write(row, 5, '{:.2f}'.format(round(sum_total_cost, 2)), format_number)
            sheet.write(row, 6, '{:.2f}'.format(round(sum_profit, 2)), format_number)
            sheet.write(row, 7, sum_formatted_value, format_number)


        elif data['document_type'] == 'brand':
            sheet.merge_range('A2:H2', "รายงานจัดลำดับยอดขายตามยี่ห้อ", format_footerC_bold2)
            domain = [('active','=',True)]
            if data['brand_id']:
                domain += [('product_brand_id','in',data['brand_id'])]

            sale_detail_all = self.env['sale.order'].search(filter_option)
            product_filter_brand_all = self.env['product.template'].search(domain)
            order_line_detail = self.env['sale.order.line'].search([("order_id","in",sale_detail_all.ids),("product_template_id","in",product_filter_brand_all.ids)])

            brand_id_data = {}
            for order in order_line_detail:
                brand_id = order.product_id.product_brand_id.name
                if brand_id not in brand_id_data:
                    brand_id_data[brand_id] = {
                        'total_brand_id_quantity': 0,
                        'total_free_product_qty': 0,
                        'total_brand_id_amount': 0,
                        'total_cost': 0,
                        'total_profit': 0,
                    }
                if order.product_id.free_product:
                    brand_id_data[brand_id]['total_free_product_qty'] += order.product_uom_qty
                brand_id_data[brand_id]['total_brand_id_quantity'] += order.product_uom_qty
                brand_id_data[brand_id]['total_brand_id_amount'] += (order.price_unit * order.product_uom_qty)
                brand_id_data[brand_id]['total_cost'] += (order.product_id.standard_price * order.product_uom_qty)
                brand_id_data[brand_id]['total_profit'] += (order.price_unit * order.product_uom_qty) - (order.product_id.standard_price * order.product_uom_qty)
            
            row = 3 
            sheet.write(3, 0, 'ลำดับที่', format_header)
            sheet.write(3, 1, 'ประเภทสินค้า', format_header)
            sheet.write(3, 2, 'จำนวนขายสุทธิ', format_header)
            sheet.write(3, 3, 'จำนวนแถม', format_header)
            sheet.write(3, 4, 'ยอดขายสุทธิ', format_header)
            sheet.write(3, 5, 'ต้นทุน', format_header)
            sheet.write(3, 6, 'กำไร (บาท)', format_header)
            sheet.write(3, 7, 'กำไร%', format_header)

            no_count = 0
            sum_profit = 0
            sum_total_amount = 0
            sum_total_cost = 0
            for brand_id, data in brand_id_data.items():
                no_count += 1
                sum_total_amount += data['total_brand_id_amount']
                sum_total_cost += data['total_cost']
                row += 1
                sheet.write(row, 0, no_count, format_detail)
                sheet.write(row, 1, brand_id, format_detail)
                sheet.write(row, 2, '{:.2f}'.format(round(data['total_brand_id_quantity'], 2)), format_number)
                sheet.write(row, 3, '{:.2f}'.format(round(data['total_free_product_qty'], 2)), format_number)
                sheet.write(row, 4, '{:.2f}'.format(round(data['total_brand_id_amount'], 2)), format_number)
                sheet.write(row, 5, '{:.2f}'.format(round(data['total_cost'], 2)), format_number)
                sheet.write(row, 6, '{:.2f}'.format(round(data['total_profit'], 2)), format_number)
                if data['total_brand_id_amount'] == 0:
                    formatted_value = "0.00"
                else:
                    formatted_value = '{:.2f}'.format(round((data['total_profit'] / data['total_brand_id_amount']) * 100, 2))
                sheet.write(row, 7, formatted_value, format_number)


            row += 1
            sum_profit = sum_total_amount - sum_total_cost
            if sum_total_amount == 0:
                sum_formatted_value = "0.00"
            else:
                sum_formatted_value = '{:.2f}'.format(round((sum_profit/sum_total_amount)*100, 2))
            sheet.merge_range(row, 0,row,3, "รวมทั้งหมด", format_detail_center)
            sheet.write(row, 4, '{:.2f}'.format(round(sum_total_amount, 2)), format_number)
            sheet.write(row, 5, '{:.2f}'.format(round(sum_total_cost, 2)), format_number)
            sheet.write(row, 6, '{:.2f}'.format(round(sum_profit, 2)), format_number)
            sheet.write(row, 7, sum_formatted_value, format_number)

            
        elif data['document_type'] == 'customer':
            sheet.merge_range('A2:H2', "รายงานจัดลําดับยอดขายตามลูกค้า", format_footerC_bold2)
            if data['partner_id']:
                filter_option += [('partner_id','in',data['partner_id'])]

            sale_detail_all = self.env['sale.order'].search(filter_option)

            sales_data = {}
            for order in sale_detail_all:
                customer_name = order.partner_id.name
                if customer_name not in sales_data:
                    sales_data[customer_name] = {
                        'total_sales_quantity': 0,
                        'total_sales_amount': 0,
                        'total_free_product_qty': 0,
                        'total_cost': 0,
                        'total_profit': 0,
                    }
                for line in order.order_line:
                    if line.product_id.free_product:
                        sales_data[customer_name]['total_free_product_qty'] += line.product_uom_qty
                
                sales_data[customer_name]['total_sales_quantity'] += sum(order.order_line.mapped('product_uom_qty'))
                sales_data[customer_name]['total_sales_amount'] += order.amount_untaxed
                sales_data[customer_name]['total_cost'] += sum(order.order_line.mapped(lambda line: line.product_id.standard_price * line.product_uom_qty))
                sales_data[customer_name]['total_profit'] += sum(order.order_line.mapped(lambda line: line.price_subtotal - (line.product_id.standard_price * line.product_uom_qty)))
            
            row = 3 
            sheet.write(3, 0, 'ลำดับที่', format_header)
            sheet.write(3, 1, 'ชื่อลูกค้า', format_header)
            sheet.write(3, 2, 'จำนวนขายสุทธิ', format_header)
            sheet.write(3, 3, 'จำนวนแถม', format_header)
            sheet.write(3, 4, 'ยอดขายสุทธิ', format_header)
            sheet.write(3, 5, 'ต้นทุน', format_header)
            sheet.write(3, 6, 'กำไร (บาท)', format_header)
            sheet.write(3, 7, 'กำไร%', format_header)

            no_count = 0
            sum_profit = 0
            sum_total_sales_amount = 0
            sum_total_cost = 0
            for customer_name, data in sales_data.items():
                no_count += 1
                sum_total_sales_amount += data['total_sales_amount']
                sum_total_cost += data['total_cost']

                row += 1
                sheet.write(row, 0, no_count, format_detail)
                sheet.write(row, 1, customer_name, format_detail)
                sheet.write(row, 2, '{:.2f}'.format(round(data['total_sales_quantity'], 2)), format_number)
                sheet.write(row, 3, '{:.2f}'.format(round(data['total_free_product_qty'], 2)), format_number)
                sheet.write(row, 4, '{:.2f}'.format(round(data['total_sales_amount'], 2)), format_number)
                sheet.write(row, 5, '{:.2f}'.format(round(data['total_cost'], 2)), format_number)
                sheet.write(row, 6, '{:.2f}'.format(round(data['total_profit'], 2)), format_number)
                if data['total_sales_amount'] == 0:
                    formatted_value = "0.00"
                else:
                    formatted_value = '{:.2f}'.format(round((data['total_profit'] / data['total_sales_amount']) * 100, 2))
                sheet.write(row, 7, formatted_value, format_number)


            row += 1
            sum_profit = sum_total_sales_amount - sum_total_cost
            if sum_total_sales_amount == 0:
                sum_formatted_value = "0.00"
            else:
                sum_formatted_value = '{:.2f}'.format(round((sum_profit/sum_total_sales_amount)*100, 2))

            sheet.merge_range(row, 0,row,3, "รวมทั้งหมด", format_detail_center)
            sheet.write(row, 4, '{:.2f}'.format(round(sum_total_sales_amount, 2)), format_number)
            sheet.write(row, 5, '{:.2f}'.format(round(sum_total_cost, 2)), format_number)
            sheet.write(row, 6, '{:.2f}'.format(round(sum_profit, 2)), format_number)
            sheet.write(row, 7, sum_formatted_value, format_number)





        
