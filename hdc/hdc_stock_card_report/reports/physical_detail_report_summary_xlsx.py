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
from dateutil.relativedelta import relativedelta

class PhysicalDetailSummaryXlsx(models.AbstractModel):
    _name = 'report.physical_detail_report_summary_xlsx'
    _description = 'report.physical_detail_report_summary_xlsx'
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
        warehouse_ids = partners.warehouse_ids
        start_date = start_date.strftime("%Y-%m-%d 00:00:00")
        to_date = to_date.strftime("%Y-%m-%d 23:59:59")
        location_ids = partners.location_ids

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
        data_cell_format_left = workbook.add_format({
            'align': 'left',
            'border': False,
        })
        data_cell_format_left.set_font_size(9)
        data_cell_format_left.set_align('vcenter')
        data_cell_format_left.set_font_name('Kanit')
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

        data_bold_cell_format_number = workbook.add_format({
            'num_format': '#,##0.00',
            'bold': True,
            'align': 'right',
        })
        data_bold_cell_format_number.set_font_size(9)
        data_bold_cell_format_number.set_align('vcenter')
        data_bold_cell_format_number.set_font_name('Kanit')

        grandtotal_cell_format = workbook.add_format({
            'bold': True,
            'align': 'left',
            'bg_color': '#92D050',
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
        report_name = ("Physical (Detail)")
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
        
        sheet.write(1, 2, 'SPE Stock card - Physical (Summary)',top_cell_format)
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
        
        sheet.write(10,0, 'รหัสสินค้า', head_cell_format)
        sheet.write(10,1, 'ชื่อสินค้า.', head_cell_format)
        sheet.write(10,2, 'Config', head_cell_format)
        sheet.write(10,3, 'หน่วย', head_cell_format)

        sheet.merge_range('E9:F10', 'ยอดยกมา', head_cell_format)
        sheet.merge_range('E11:F11', 'จำนวน', head_sub_cell_format)

        sheet.merge_range('G9:H10', 'รับเข้า', head_cell_format)
        sheet.merge_range('G11:H11', 'จำนวน', head_sub_cell_format)

        sheet.merge_range('I9:J10', 'จ่ายออก', head_cell_format)
        sheet.merge_range('I11:J11', 'จำนวน', head_sub_cell_format)

        sheet.merge_range('K9:L10', 'ยอดคงเหลือ', head_cell_format)
        sheet.merge_range('K11:L11', 'จำนวน', head_sub_cell_format)

        column_widths = {
            0: 15,  # A
            1: 40,  # B
            2: 15,  # C
            3: 15,  # D
            4: 15,  # E
            5: 15,  # F
            6: 15,  # G
            7: 15,  # H
            8: 15,  # I
            9: 15,  # J
            10: 15,  # K
            11: 15,  # L
            12: 15,  # M
            13: 15,  # N
            14: 15,  # O
            15: 15,  # P
            16: 15, # Q
            17: 15, # R
            18: 15, # S
            19: 15, # T
        }

        for col, width in column_widths.items():
            sheet.set_column(col, col, width)

        search = []

        row = 10
        number = 0
        in_total = 0
        out_total = 0
        qty_total = 0
        grand_before_total = 0
        first_product = True
        internal_total_qty = 0
        transit_total_qty = 0
        amount_total = 0
        grand_amount_total = 0

        for i, product_ids in enumerate(product_id):
            physical_detail_results_product = []
            physical_detail_results_location = []
            before_total = 0
            amount_qty = 0
            amount_before = 0
            qty_9 = 0
            qty_11 = 0
            qty_available = 0

            if location_ids:
                stock_quant = self.env['stock.quant'].search(
                    [('product_id', '=', product_ids.id),('location_id', 'in',location_ids.ids),('location_id.usage', 'in',('internal', 'transit'))])
                        
            else:
                if warehouse_ids:
                    stock_quant = self.env['stock.quant'].search(
                    [('product_id', '=', product_ids.id),('warehouse_id', 'in',warehouse_ids.ids),('location_id.usage', 'in',('internal', 'transit'))])

                else:
                    stock_quant = self.env['stock.quant'].search(
                    [('product_id', '=', product_ids.id),('location_id.usage', 'in',('internal', 'transit'))])
                    
            for sq in stock_quant:
                if sq.location_id.id not in physical_detail_results_location:
                    physical_detail_results_location.append(sq.location_id.id)
            
            if date_to and date_from:
                stock_move_id = self.env['stock.move.line'].search(
                            [('date', '<=', date_to), ('date', '>=', date_from), ('state', '=', 'done'),
                            ('product_id', '=', product_ids.id)], order="date")
                if location_ids:
                    stock_quant = self.env['stock.quant'].search(
                    [('create_date', '<', date_from), ('product_id', '=', product_ids.id),('location_id', 'in', location_ids.ids)])

                else:
                    if warehouse_ids:
                        stock_quant = self.env['stock.quant'].search(
                        [('create_date', '<', date_from), ('product_id', '=', product_ids.id), ('warehouse_id', 'in', warehouse_ids.ids),('location_id.usage', 'in', ('internal', 'transit'))])

                    else:
                        stock_quant = self.env['stock.quant'].search(
                        [('create_date', '<', date_from), ('product_id', '=', product_ids.id),('location_id.usage', 'in', ('internal', 'transit'))])

            else:
                stock_move_id = self.env['stock.move.line'].search(
                            [('state', '=', 'done'), ('product_id', '=', product_ids.id),], order="date")
            
            if stock_move_id:
                if stock_quant:
                    for before_stock_quant_ids in stock_quant:
                        amount_before += before_stock_quant_ids.quantity
                
                qty_available = product_ids._compute_quantities_dict_warehouse_location_lot(lot_id=None, owner_id=None, package_id=None,to_date=date_from)
                if location_ids:
                    qty_available = product_ids._compute_quantities_dict_warehouse_location_lot(lot_id=None, owner_id=None, package_id=None,to_date=date_from,warehouse_id=warehouse_ids,location_id=location_ids)
                else:
                    if warehouse_ids:
                        qty_available = product_ids._compute_quantities_dict_warehouse_location_lot(lot_id=None, owner_id=None, package_id=None,to_date=date_from,warehouse_id=warehouse_ids)

                before_total = before_total + amount_before
                amount_qty = qty_available
                
                qty_total += amount_qty
                if first_product == False:
                    grand_amount_total = grand_amount_total + amount_total 
                    first_product == True    
                    internal_total_qty = 0
                    transit_total_qty = 0
                
                first_product = False              
                
                for stock_move_ids in stock_move_id:
                    stock_move_line_ids = stock_move_ids
                    product_uom_id = stock_move_line_ids.product_uom_id.name
                        
                    qty = stock_move_line_ids.product_uom_id._compute_quantity(stock_move_line_ids.qty_done, stock_move_line_ids.product_id.uom_id)

                    location_id_check = False
                    location_dest_id_check = False
                    if location_ids:
                        if stock_move_line_ids.location_id.id in location_ids.ids:
                            location_id_check = True
                        if stock_move_line_ids.location_dest_id.id in location_ids.ids:
                            location_dest_id_check = True
                    elif warehouse_ids:
                        if stock_move_line_ids.location_id.warehouse_id.id in warehouse_ids.ids:
                            location_id_check = True
                        if stock_move_line_ids.location_dest_id.warehouse_id.id in warehouse_ids.ids:
                            location_dest_id_check = True
                    else:
                        location_id_check = True
                        location_dest_id_check = True

                    if stock_move_ids.location_id.usage in ('internal', 'transit') and location_id_check:
                        amount_qty = amount_qty - qty
                        qty_9 = False
                        qty_11 = qty

                        data_list = {
                            "product_id":product_ids.id,
                            "location_dest_id":stock_move_line_ids.location_id.id,
                            "amount_qty":amount_qty,
                            "qty_in":qty_9,
                            "qty_out":qty_11,
                            "qty_available":qty_available,
                        }
                        physical_detail_results_product.append(data_list)
                        if stock_move_line_ids.location_id.id not in physical_detail_results_location:
                            physical_detail_results_location.append(stock_move_line_ids.location_id.id)
                    if stock_move_ids.location_dest_id.usage in ('internal', 'transit') and location_dest_id_check:
                        amount_qty = amount_qty + qty
                        qty_9 = qty
                        qty_11 = False

                        data_list = {
                            "product_id":product_ids.id,
                            "location_dest_id":stock_move_line_ids.location_dest_id.id,
                            "amount_qty":amount_qty,
                            "qty_in":qty_9,
                            "qty_out":qty_11,
                            "qty_available":qty_available,
                        }
                        physical_detail_results_product.append(data_list)
                        if stock_move_line_ids.location_dest_id.id not in physical_detail_results_location:
                            physical_detail_results_location.append(stock_move_line_ids.location_dest_id.id)

            for locat in physical_detail_results_location:
                internal_total_qty = 0
                transit_total_qty = 0
                amount_total = 0
                qty_available_summary = 0
                for data in physical_detail_results_product:
                    if data["location_dest_id"] == locat:
                        internal_total_qty = internal_total_qty + data["qty_in"]
                        transit_total_qty = transit_total_qty + data["qty_out"]         

                location_summary = self.env['stock.location'].search([('id', '=', locat)])
                qty_available_summary = product_ids._compute_quantities_dict_warehouse_location_lot(lot_id=None, owner_id=None, package_id=None,to_date=date_from,warehouse_id=location_summary.warehouse_id,location_id=location_summary)
                amount_total = qty_available_summary + internal_total_qty - transit_total_qty

                row += 1
                data_list = [
                            product_ids.default_code or "",
                            product_ids.name or "",]
                sheet.write_row(row,0, data_list,data_cell_format_left)
                sheet.write(row,2, location_summary.complete_name or "",data_cell_format)
                sheet.write(row,3, product_ids.uom_id.name,data_cell_format)

                merge_row = 'E' + str(row + 1) + ':F' + str(row + 1)
                sheet.merge_range(merge_row, qty_available_summary or "",data_cell_number_format)
                
                merge_row1 = 'G' + str(row + 1) + ':H' + str(row + 1)
                sheet.merge_range(merge_row1, internal_total_qty or "",data_cell_number_format)

                merge_row2 = 'I' + str(row + 1) + ':J' + str(row + 1)
                sheet.merge_range(merge_row2, transit_total_qty or "",data_cell_number_format)

                merge_row3 = 'K' + str(row + 1) + ':L' + str(row + 1)
                sheet.merge_range(merge_row3, amount_total or "",data_cell_number_format)

                row += 1
                merge_row = 'E' + str(row + 1) + ':F' + str(row + 1)
                sheet.merge_range(merge_row, "TOTAL",data_cell_format)
                
                merge_row1 = 'G' + str(row + 1) + ':H' + str(row + 1)
                sheet.merge_range(merge_row1, internal_total_qty or 0,data_cell_number_format)

                merge_row2 = 'I' + str(row + 1) + ':J' + str(row + 1)
                sheet.merge_range(merge_row2, transit_total_qty or 0,data_cell_number_format)

                merge_row3 = 'K' + str(row + 1) + ':L' + str(row + 1)
                sheet.merge_range(merge_row3, amount_total or 0,data_cell_number_format)

                grand_before_total = grand_before_total + qty_available_summary
                in_total = in_total + internal_total_qty
                out_total = out_total + transit_total_qty
                grand_amount_total = grand_before_total + in_total - out_total 
        row += 1
        data_list = ["",
                    "",
                    "",
                    "",
                    ]
        sheet.write_row(row,0, data_list,format_footerC_bold)  

        sheet.write(row,1, "GRAND TOTAL", grandtotal_cell_format)

        merge_row = 'E' + str(row + 1) + ':F' + str(row + 1)
        sheet.merge_range(merge_row, grand_before_total or 0,format_footerC_bold)

        merge_row1 = 'G' + str(row + 1) + ':H' + str(row + 1)
        sheet.merge_range(merge_row1, in_total or 0,format_footerC_bold)

        merge_row2 = 'I' + str(row + 1) + ':J' + str(row + 1)
        sheet.merge_range(merge_row2, out_total or 0,format_footerC_bold)

        merge_row3 = 'K' + str(row + 1) + ':L' + str(row + 1)
        sheet.merge_range(merge_row3, grand_amount_total or 0,format_footerC_bold)

        