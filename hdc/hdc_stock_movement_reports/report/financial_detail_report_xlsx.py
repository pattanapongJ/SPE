# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
import pytz
import datetime
from datetime import datetime, date, time
from decimal import Decimal, ROUND_HALF_UP
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError, except_orm

import io
import base64
from PIL import Image

class FinancialDetailXlsx(models.AbstractModel):
    _name = 'report.financial_detail_report_xlsx'
    _description = 'report.financial_detail_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    

    def get_selection(self,pd_type):
        # for record in self:
        stored_value = pd_type
        if stored_value is None or stored_value is False:
            display_value = ''
        else:
            selection_list = self.env["product.template"]._fields["type"].selection
            selection_dict = dict(selection_list)
            display_value = selection_dict.get(stored_value, '')

        return display_value

    def generate_xlsx_report(self, workbook, data, partners):

        product_id = partners.product_id
        start_date = partners.date_from
        to_date = partners.date_to
        date_from = partners.date_from
        date_to = partners.date_to
        warehouse_id = partners.warehouse_id
        start_date = start_date.strftime("%Y-%m-%d 00:00:00")
        to_date = to_date.strftime("%Y-%m-%d 23:59:59")

        if product_id:
            product_id = self.env['product.product'].search([('id', '=', product_id.ids), ('type', '!=', 'service')])
        else:
            product_id = self.env['product.product'].search([('type', '!=', 'service'),('write_date', '<=', date_to), ('write_date', '>=', date_from)])

        res_users = self.env['res.users'].search([('id', '=', self.env.uid)])

        # format
        top_cell_format = workbook.add_format({
            'bold': True,
            'align': 'center',
        })
        top_cell_format.set_font_size(9)
        top_cell_format.set_align('vcenter')
        top_cell_format.set_font_name('Kanit')
        head_top_cell_format = workbook.add_format({
            'align': 'left',
            'border': True,
            'bg_color': '#92D050'
        })
        head_top_cell_format.set_font_size(9)
        head_top_cell_format.set_align('vleft')
        head_top_cell_format.set_font_name('Kanit')
        data_cell_format = workbook.add_format({
            'align': 'right',
            'border': False,
        })
        data_cell_format.set_font_size(9)
        data_cell_format.set_align('vcenter')
        data_cell_format.set_font_name('Kanit')
        data_cell_number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'border': False,
        })
        data_cell_number_format.set_font_size(9)
        data_cell_number_format.set_align('vcenter')
        data_cell_number_format.set_font_name('Kanit')


        
        head_cell_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': True,
            'bg_color': '#92D050'
        })
        head_cell_format.set_font_size(9)
        head_cell_format.set_align('vcenter')
        head_cell_format.set_font_name('Kanit')
        head_cell_format_no_color = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': True,
        })
        head_cell_format_no_color.set_font_size(9)
        head_cell_format_no_color.set_align('vcenter')
        head_cell_format_no_color.set_font_name('Kanit')

        head_sub_cell_format = workbook.add_format({
            'align': 'center',
            'border': True,
        })
        head_sub_cell_format.set_font_size(9)
        head_sub_cell_format.set_align('vcenter')
        head_sub_cell_format.set_font_name('Kanit')
        data_bold_cell_format = workbook.add_format({
            'bold': True,
            'align': 'left',
        })
        data_bold_cell_format.set_font_size(9)
        data_bold_cell_format.set_align('vcenter')
        data_bold_cell_format.set_font_name('Kanit')
        grandtotal_cell_format = workbook.add_format({
            'bold': True,
            'align': 'left',
            'bg_color': '#FF0000',
            'top': True
        })
        grandtotal_cell_format.set_font_size(9)
        grandtotal_cell_format.set_align('vcenter')
        grandtotal_cell_format.set_font_name('Kanit')

        format_footerC_bold = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right', 
            'top': True
        })
        format_footerC_bold.set_font_size(9)
        format_footerC_bold.set_align('vcenter')
        format_footerC_bold.set_font_name('Kanit')

        datetime_format = workbook.add_format({'align': 'right'})
        datetime_format.set_font_size(9)
        datetime_format.set_align('vcenter')
        datetime_format.set_font_name('Kanit')

        # report name
        report_name = ("Financial (Detail)")
        sheet = workbook.add_worksheet(report_name)
        image_company = partners.company_id.logo
        if image_company:
            image = io.BytesIO(base64.b64decode(image_company))
        else:
            image = False

        if image:
            
            product_image = image
            imageTosize = Image.open(product_image)
            x_size = imageTosize.size[0]
            y_size = imageTosize.size[1]
            max_size = x_size if x_size > y_size else y_size
            xy_max_size = 96
            scale = xy_max_size/max_size
            sheet.insert_image(0 ,0 ,'image' , {
                'image_data': image,
                'x_scale': scale,
                'y_scale': scale,
                'x_offset': 10, 
                'y_offset': 10
            })
        
        sheet.write(1, 2, 'SPE Stock card - Financial (Detail)',top_cell_format)
        sheet.write(3, 2, 'Saeng Charoen Group',top_cell_format)
        sheet.write(3, 14, 'PRINT DATE: ',head_top_cell_format)

        current_dateTime = datetime.now()
        sheet.write(3, 15, current_dateTime.strftime('%d-%m-%y'),datetime_format)
        sheet.write(3, 16, current_dateTime.strftime('%H:%M:%S'),datetime_format)
        
        sheet.set_row(0, 20)
        sheet.set_row(1, 15)
        sheet.set_row(2, 15)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 3, 20)
        sheet.set_column(4, 4, 40)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 8, 15)
        sheet.set_column(9, 12, 15)

        # date from - date to
        day_to = ''
        text_month_to = ''
        year_to = ''
        day_from = ''
        text_month_from = ''
        year_from = ''

        if date_from:
            day_from = str(date_from).split('-')[2]
            month_from = str(date_from).split('-')[1]
            year_from = str(date_from).split('-')[0]
            if month_from:
                if int(month_from) == 1:
                    text_month_from = 'Jan'
                if int(month_from) == 2:
                    text_month_from = 'Feb'
                if int(month_from) == 3:
                    text_month_from = 'Mar'
                if int(month_from) == 4:
                    text_month_from = 'Apr'
                if int(month_from) == 5:
                    text_month_from = 'May'
                if int(month_from) == 6:
                    text_month_from = 'June'
                if int(month_from) == 7:
                    text_month_from = 'July'
                if int(month_from) == 8:
                    text_month_from = 'Aug'
                if int(month_from) == 9:
                    text_month_from = 'Sept'
                if int(month_from) == 10:
                    text_month_from = 'Oct'
                if int(month_from) == 11:
                    text_month_from = 'Nov'
                if int(month_from) == 12:
                    text_month_from = 'Dec'
            if year_from:
                year_from = int(year_from)

        if date_to:
            day_to = str(date_to).split('-')[2]
            month_to = str(date_to).split('-')[1]
            year_to = str(date_to).split('-')[0]
            if month_to:
                if int(month_to) == 1:
                    text_month_to = 'Jan'
                if int(month_to) == 2:
                    text_month_to = 'Feb'
                if int(month_to) == 3:
                    text_month_to = 'Mar'
                if int(month_to) == 4:
                    text_month_to = 'Apr'
                if int(month_to) == 5:
                    text_month_to = 'May'
                if int(month_to) == 6:
                    text_month_to = 'June'
                if int(month_to) == 7:
                    text_month_to = 'July'
                if int(month_to) == 8:
                    text_month_to = 'Aug'
                if int(month_to) == 9:
                    text_month_to = 'Sept'
                if int(month_to) == 10:
                    text_month_to = 'Oct'
                if int(month_to) == 11:
                    text_month_to = 'Nov'
                if int(month_to) == 12:
                    text_month_to = 'Dec'
            if year_to:
                year_to = int(year_to)

        

        sheet.write(5, 1, 'ตั้งแต่ช่วงวันที่',head_top_cell_format)
        sheet.write(5, 2, (str(day_from) + ' ' + str(text_month_from) + ' ' + str(year_from)),datetime_format)
        sheet.write(5, 4, 'ถึง',head_top_cell_format)
        sheet.write(5, 5, (str(day_to) + ' ' + str(text_month_to) + ' ' + str(year_to)),datetime_format)

        date_show = 'จากวันที่ ' + str(day_from) + ' ' + str(text_month_from) + ' ' + str(year_from) + ' ถึง ' + str(
            day_to) + ' ' + str(text_month_to) + ' ' + str(year_to)

        
        sheet.write(10,0, 'DATE', head_cell_format)
        sheet.write(10,1, 'REF.No.', head_cell_format)
        sheet.write(10,2, 'CustVendAccount', head_cell_format)
        sheet.write(10,3, 'Unit', head_cell_format)
        sheet.write(10,4, '', head_cell_format_no_color)
        sheet.write(10,5, 'Location', head_cell_format)

        sheet.merge_range('G9:I10', 'รับเข้า', head_cell_format)
        sheet.write(10,6, 'จำนวน', head_sub_cell_format)
        sheet.write(10,7, 'ราคา-หน่วย', head_sub_cell_format)
        sheet.write(10,8, 'มูลค่า', head_sub_cell_format)

        sheet.merge_range('J9:L10', 'จ่ายออก', head_cell_format)
        sheet.write(10,9, 'จำนวน', head_sub_cell_format)
        sheet.write(10,10, 'ราคา-หน่วย', head_sub_cell_format)
        sheet.write(10,11, 'มูลค่า', head_sub_cell_format)

        sheet.merge_range('M9:O10', 'ยอดคงเหลือ', head_cell_format)
        sheet.write(10,12, 'จำนวน', head_sub_cell_format)
        sheet.write(10,13, 'ราคา-หน่วย', head_sub_cell_format)
        sheet.write(10,14, 'มูลค่า', head_sub_cell_format)

        column_widths = {
            0: 15,  # A
            1: 20,  # B
            2: 40,  # C
            3: 10,  # D
            4: 15,  # E
            5: 30,  # F
            6: 15,  # G
            7: 15,  # H
            8: 15,  # I
            9: 15,  # J
            10: 15,  # K
            11: 15,  # L
            12: 15,  # M
            13: 15, # N
            14: 15, # O
            15: 15, # P
            16: 15, # Q
        }

        for col, width in column_widths.items():
            sheet.set_column(col, col, width)

        search = []

        row = 10
        number = 0
        in_total = 0
        out_total = 0
        qty_total = 0
        before_total_sum = 0
        first_product = True
        internal_total_qty = 0
        internal_total_price = 0
        transit_total_qty = 0
        transit_total_price = 0
        in_total_price = 0
        out_total_price = 0
        amount_total = 0
        cost_price = 0
        amount_total_price = 0
        grand_amount_total = 0
        grand_amount_price_total = 0

        for i, product_ids in enumerate(product_id):
            before_total = 0
            amount_qty = 0
            in_amount = 0
            out_amount = 0
            amount_before = 0
            qty_9 = None
            qty_11 = None
            pd_type_name = ""
            
            if date_to and date_from:

                if warehouse_id:
                    stock_quant = self.env['stock.quant'].search(
                    [('create_date', '<', date_from), ('product_id', '=', product_ids.id), ('warehouse_id', '=', warehouse_id.id),('location_id.usage', 'in', ('internal', 'transit'))])

                    stock_move_id = self.env['stock.move.line'].search(
                    [('date', '<=', date_to), ('date', '>=', date_from), ('state', '=', 'done'), ('move_id.warehouse_id', '=', warehouse_id.id),
                     ('product_id', '=', product_ids.id)], order="date")

                else:
                    stock_quant = self.env['stock.quant'].search(
                    [('create_date', '<', date_from), ('product_id', '=', product_ids.id),('location_id.usage', 'in', ('internal', 'transit'))])

                    stock_move_id = self.env['stock.move.line'].search(
                        [('date', '<=', date_to), ('date', '>=', date_from), ('state', '=', 'done'),
                        ('product_id', '=', product_ids.id)], order="date")

            else:
                stock_movebefore_id = False
                
                if warehouse_id:
                    stock_move_id = self.env['stock.move.line'].search(
                        [('state', '=', 'done'), ('product_id', '=', product_ids.id), ('move_id.warehouse_id', '=', warehouse_id.id), ('location_id.usage', 'not in', ('internal', 'transit')), ('location_dest_id.usage', 'in', ('internal', 'transit'))], order="date")
                
                else:
                    stock_move_id = self.env['stock.move.line'].search(
                        [('state', '=', 'done'), ('product_id', '=', product_ids.id), ('location_id.usage', 'not in', ('internal', 'transit')), ('location_dest_id.usage', 'in', ('internal', 'transit'))], order="date")
            
            if stock_move_id:
                row += 1

                if stock_quant:
                    for before_stock_quant_ids in stock_quant:
                        amount_before += before_stock_quant_ids.quantity
                before_total = before_total + amount_before
                amount_qty = before_total
                qty_total += amount_qty
                if first_product == False:
                    in_total_price = in_total_price + internal_total_price
                    out_total_price = out_total_price + transit_total_price
                    grand_amount_total = grand_amount_total + amount_total 
                    grand_amount_price_total = grand_amount_price_total + amount_price
                    sheet.write(row,4, "TOTAL", grandtotal_cell_format)
                    data_list = [
                                internal_total_qty or "-",
                                "-",
                                internal_total_price or "-",
                                transit_total_qty or "-",
                                "-",
                                transit_total_price or "-",
                                amount_total or "-", 
                                cost_price or "-", 
                                amount_total_price or "-", 
                                ]
                
                    sheet.write_row(row,6, data_list,data_cell_number_format)  
                    row += 1 
                    first_product == True    
                    internal_total_qty = 0
                    internal_total_price = 0
                    transit_total_qty = 0
                    transit_total_price = 0 


                data_list = [product_ids.default_code or "",
                                "",
                                product_ids.name or "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                ]
                
                sheet.write_row(row,0, data_list,data_bold_cell_format)  
                first_product = False              
                
                for stock_move_ids in stock_move_id:
                    mo_id = self.env['mrp.production'].search([('name', '=', stock_move_ids.origin)],limit=1)
                    stock_move_line_ids = stock_move_ids
                    sale_price = stock_move_line_ids.sale_price
                    company_id = stock_move_line_ids.company_id.name
                    product_uom_id = stock_move_line_ids.product_uom_id.name
                    location_dest_id = stock_move_line_ids.location_dest_id.complete_name
                    if stock_move_line_ids.move_id.sale_line_id:
                        qty = stock_move_line_ids.product_uom_id._compute_quantity(stock_move_line_ids.qty_done, stock_move_line_ids.move_id.sale_line_id.product_uom)
                        unit_price = stock_move_line_ids.move_id.sale_line_id.price_reduce_taxinc
                    else:
                        qty = stock_move_line_ids.product_uom_id._compute_quantity(stock_move_line_ids.qty_done, stock_move_line_ids.product_id.uom_id)
                        unit_price = stock_move_line_ids.product_id.list_price
                    if stock_move_ids.location_id.usage not in ('internal', 'transit') and stock_move_ids.location_dest_id.usage in ('internal', 'transit'):
                        row += 1
                        number += 1
                        

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            amount_qty = amount_qty + qty
                            in_amount = in_amount + qty

                            qty_9 = qty
                            internal_total_qty = internal_total_qty + qty_9
                            internal_total_price = internal_total_price + sale_price

                        elif stock_move_ids.location_id.usage == 'internal':
                            amount_qty = amount_qty - qty
                            out_amount = out_amount + qty

                            qty_11 = qty
                            transit_total_qty = transit_total_qty + qty_11
                            transit_total_price = transit_total_price + sale_price

                        qty_total += amount_qty
                        amount_price = amount_qty * product_ids.standard_price
                        if product_ids.type:
                            pd_type = product_ids.type
                            pd_type_name = self.get_selection(pd_type)

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            
                            data_list_1 = [
                                    str(stock_move_ids.date.strftime('%d-%m-%y')), 
                                    product_ids.default_code or '',
                                    company_id or '',
                                    product_uom_id,
                                    "",
                                    location_dest_id or "-"
                                    ]
                            data_list_1_2 = [
                                    qty_9 or "-", 
                                    unit_price or "-", 
                                    sale_price or "-", 
                                    "-", 
                                    "-",
                                    "-", 
                                    amount_qty or "-", 
                                    product_ids.standard_price or "-", 
                                    amount_price or "-", 
                                    ]
                        elif stock_move_ids.location_id.usage == 'internal':
                            data_list_1 = [
                                    str(stock_move_ids.date.strftime('%d-%m-%y')), 
                                    product_ids.default_code or '',
                                    company_id or '',
                                    product_uom_id,
                                    "",
                                    location_dest_id or "-"
                                    ]
                            data_list_1_2 = [
                                    "-", 
                                    "-", 
                                    "-", 
                                    qty_11 or "-", 
                                    unit_price or "-",
                                    sale_price or "-", 
                                    amount_qty or "-", 
                                    product_ids.standard_price or "-",
                                    amount_price or "-", 
                                    ]

                        sheet.write_row(row,0, data_list_1,data_cell_format)
                        sheet.write_row(row,6, data_list_1_2,data_cell_number_format)

                    elif stock_move_ids.location_id.usage in ('internal', 'transit') and stock_move_ids.location_dest_id.usage not in ('internal', 'transit'):
                        row += 1
                        number += 1

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            amount_qty = amount_qty + qty
                            in_amount = in_amount + qty

                            qty_9 = qty
                            internal_total_qty = internal_total_qty + qty_9
                            internal_total_price = internal_total_price + sale_price

                        elif stock_move_ids.location_id.usage == 'internal':
                            amount_qty = amount_qty - qty
                            out_amount = out_amount + qty

                            qty_11 = qty
                            transit_total_qty = transit_total_qty + qty_11
                            transit_total_price = transit_total_price + sale_price

                        qty_total += amount_qty
                        amount_price = amount_qty * product_ids.standard_price
                        if product_ids.type:
                            pd_type = product_ids.type
                            pd_type_name = self.get_selection(pd_type)

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            data_list_2 = [str(stock_move_ids.date.strftime('%d-%m-%y')),
                                            product_ids.default_code or '',
                                            company_id or '',
                                            product_uom_id,
                                            "",
                                            location_dest_id or "-",
                                            ]
                            data_list_2_2 = [
                                            qty_9 or "-",
                                            unit_price or "-",
                                            sale_price or "-",
                                            "-",
                                            "-",
                                            "-",
                                            amount_qty or "-",
                                            product_ids.standard_price or "-",
                                            amount_price or "-",
                                        ]
                        elif stock_move_ids.location_id.usage == 'internal':
                            data_list_2 = [str(stock_move_ids.date.strftime('%d-%m-%y')),
                                            product_ids.default_code or '',
                                            company_id or '',
                                            product_uom_id,
                                            "",
                                            location_dest_id or "-",
                                            ]
                            data_list_2_2 = [
                                            "-",
                                            "-",
                                            "-",
                                            qty_11 or "-",
                                            unit_price or "-",
                                            sale_price or "-",
                                            amount_qty or "-",
                                            product_ids.standard_price or "-",
                                            amount_price or "-",
                                        ]
                        
                        sheet.write_row(row,0, data_list_2,data_cell_format)
                        sheet.write_row(row,6, data_list_2_2,data_cell_number_format)
                    cost_price = product_ids.standard_price
                    amount_total = amount_qty
                    amount_total_price = cost_price * amount_total

                in_total = in_total + in_amount
                out_total = out_total + out_amount
            before_total_sum += before_total
        row += 1
        sheet.write(row,4, "TOTAL", grandtotal_cell_format)
        in_total_price = in_total_price + internal_total_price
        out_total_price = out_total_price + transit_total_price
        grand_amount_total = grand_amount_total + amount_total 
        grand_amount_price_total = grand_amount_price_total + amount_price
        data_list = [
                    internal_total_qty or "-",
                    "-",
                    internal_total_price or "-",
                    transit_total_qty or "-",
                    "-",
                    transit_total_price or "-",
                    amount_total or "-", 
                    cost_price or "-", 
                    amount_total_price or "-", 
                    ]
                
        sheet.write_row(row,6, data_list,data_cell_number_format)  
        row += 1

        data_list = ["",
                    "",
                    "",
                    "",
                    "",
                    "",
                    in_total or "-",
                    "-",
                    in_total_price or "-",
                    out_total or "-",
                    "-",
                    out_total_price or "-",
                    grand_amount_total or "", 
                    "-", 
                    grand_amount_price_total or "-", 
                    ]
                
        sheet.write_row(row,0, data_list,format_footerC_bold)  
        sheet.write(row,2, "GRAND TOTAL", grandtotal_cell_format)
        