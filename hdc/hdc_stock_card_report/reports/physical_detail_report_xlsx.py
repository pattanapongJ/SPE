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

class PhysicalDetailXlsx(models.AbstractModel):
    _name = 'report.physical_detail_report_xlsx'
    _description = 'report.physical_detail_report_xlsx'
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
    
    def get_reference_detail(self,reference=False):
        operation_type={
            "OUTC24ITT":"Delivery Order Inter Transfer",
            "OUTCFAC1ITT":"Delivery Order Inter Transfer",
            "OUTCGIITT":"Delivery Order Inter Transfer",
            "OUTCLLKITT":"Delivery Order Inter Transfer",
            "OUTCNPTITT":"Delivery Order Inter Transfer",
            "OUTCRETITT":"Delivery Order Inter Transfer",
            "OUTFAC3ITT":"Delivery Order Inter Transfer", 
            "INCFAC3ITT":"Receipt Order Inter Transfer",
            "INCFACITT":"Receipt Order Inter Transfer",
            "INCGIITT":"Receipt Order Inter Transfer",
            "INCLLKITT":"Receipt Order Inter Transfer",
            "INCNPTITT":"Receipt Order Inter Transfer",
            "INCRETITT":"Receipt Order Inter Transfer",
            "C24BINITT":"Receipt Order Inter Transfer",
            "C24BOUTITT":"Delivery Order Inter Transfer",
            "C24BRC":"Return Customer",
            "C24INITT":"Receipt Order Inter Transfer",
            "C24RC":"Return Customer",
            "CFAC3ITT":"C-FAC3 Inter Transfer",
            "CFACITT":"C-FAC1 Inter Transfer",
            "CGIITT":"C-GI Inter Transfer",
            "CGIRC":"Return Customer",
            "CLLITT":"CLLK Inter Transfer",
            "CLLKRC":"Return Customer",
            "CNPTITT":"C-NPT Inter Transfer",
            "CRETITT":"C-RET Inter Transfer",
            "FAC1RC":"Return Customer",
            "FAC3RC":"Return Customer",
            "NPTRC":"Return Customer",
            "RETRC":"Return Customer",
            "BF":"การเบิกสินค้า (ของแถม)",
            "BRS":"การเบิก/ยืมสินค้าภายในเครื่องมือ",
            "IN":"Receipts",
            "INT":"Internal Transfers",
            "ITT":"Inter Transfer",
            "MO":"Manufacturing",
            "OUT":"Delivery Orders",    
            "RB":"การคืนสินค้า จากการยืม",
            }
        operation_type_code = list(operation_type.keys())
        for code in operation_type_code:
            if "/"+code+"/" in reference:
                return operation_type.get(code)
        return ""

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
        
        sheet.write(1, 2, 'SPE Stock card - Physical (Detail)',top_cell_format)
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
        sheet.write(10,1, 'Source.No.', head_cell_format)
        sheet.write(10,2, 'REF.No.', head_cell_format)
        sheet.write(10,3, 'รายละเอียดของ REF.No.', head_cell_format)
        sheet.write(10,4, 'CustVendAccount', head_cell_format)
        sheet.write(10,5, 'SPE Invoice', head_cell_format)
        sheet.write(10,6, 'Unit', head_cell_format)
        sheet.write(10,7, '', head_cell_format_no_color)
        sheet.write(10,8, 'Location', head_cell_format)

        sheet.merge_range('J9:K10', 'รับเข้า', head_cell_format)
        sheet.merge_range('J11:K11', 'จำนวน', head_sub_cell_format)

        sheet.merge_range('L9:M10', 'จ่ายออก', head_cell_format)
        sheet.merge_range('L11:M11', 'จำนวน', head_sub_cell_format)

        sheet.merge_range('N9:O10', 'ยอดคงเหลือ', head_cell_format)
        sheet.merge_range('N11:O11', 'จำนวน', head_sub_cell_format)

        column_widths = {
            0: 15,  # A
            1: 20,  # B
            2: 20,  # C
            3: 30,  # D
            4: 40,  # E
            5: 20,  # F
            6: 10,  # G
            7: 15,  # H
            8: 30,  # I
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
        before_total_sum = 0
        first_product = True
        internal_total_qty = 0
        transit_total_qty = 0
        amount_total = 0
        grand_amount_total = 0

        for i, product_ids in enumerate(product_id):
            before_total = 0
            amount_qty = 0
            in_amount = 0
            out_amount = 0
            amount_before = 0
            qty_9 = None
            qty_11 = None
            qty_available = None
            
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
                row += 1
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
                    sheet.write(row,6, "TOTAL", grandtotal_cell_format)

                    merge_row = 'J' + str(row + 1) + ':K' + str(row + 1)
                    sheet.merge_range(merge_row, internal_total_qty or "-",data_cell_number_format)

                    merge_row1 = 'L' + str(row + 1) + ':M' + str(row + 1)
                    sheet.merge_range(merge_row1, transit_total_qty or "-",data_cell_number_format)

                    merge_row2 = 'N' + str(row + 1) + ':O' + str(row + 1)
                    sheet.merge_range(merge_row2, amount_total or "-",data_cell_number_format)
                    
                    row += 1 
                    first_product == True    
                    internal_total_qty = 0
                    transit_total_qty = 0
                
                data_list = [product_ids.default_code or "",
                                "",
                                "",
                                "",
                                product_ids.name or "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                ]
                
                sheet.write_row(row,0, data_list,data_bold_cell_format)  
                merge_row = 'N' + str(row + 1) + ':O' + str(row + 1)
                sheet.merge_range(merge_row, qty_available or "-",data_bold_cell_format_number)
                first_product = False              
                
                for stock_move_ids in stock_move_id:
                    stock_move_line_ids = stock_move_ids
                    company_id = stock_move_line_ids.company_id.name
                    product_uom_id = stock_move_line_ids.product_uom_id.name
                    location_dest_id = stock_move_line_ids.location_dest_id.complete_name
                    reference = stock_move_line_ids.reference
                    origin = stock_move_line_ids.origin
                    customer = ""
                    if origin:
                        sale_order = self.env['sale.order'].search(
                         [('name', '=', origin)])
                        purchase_order = self.env['purchase.order'].search(
                         [('name', '=', origin)])
                        rma_order = self.env['crm.claim.ept'].search(
                         [('code', '=', origin)])
                        if sale_order:
                            customer = sale_order.partner_id.name
                        elif purchase_order:
                            customer = purchase_order.partner_id.name
                        elif rma_order:
                            customer = rma_order.partner_id.name
                    
                    invoice = stock_move_line_ids.picking_id.invoice_ids
                    invoice_posted = invoice.search([('state', '=', 'posted'),('id','in',invoice.ids)])
                    
                    if len(invoice_posted) > 1:
                        last_date = invoice_posted[0].write_date
                        inv_last = invoice_posted[0]
                        for inv in invoice_posted:
                            if inv.write_date > last_date:
                                inv_last = inv
                        invoice_posted = inv_last
                        
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
                        row += 1
                        number += 1

                        amount_qty = amount_qty - qty
                        out_amount = out_amount + qty

                        qty_11 = qty
                        transit_total_qty = transit_total_qty + qty_11

                        data_list_1 = [
                                    str(stock_move_ids.date.strftime('%d-%m-%y')), 
                                    origin or '',
                                    reference or '',
                                    self.get_reference_detail(reference) or '',
                                    customer,
                                    invoice_posted.name or '',
                                    product_uom_id,
                                    "",
                                    stock_move_ids.location_id.complete_name or "-", 
                                    ]
                        merge_row = 'J' + str(row + 1) + ':K' + str(row + 1)
                        sheet.merge_range(merge_row, "-",data_cell_number_format)

                        merge_row1 = 'L' + str(row + 1) + ':M' + str(row + 1)
                        sheet.merge_range(merge_row1, qty_11 or "-",data_cell_number_format)
                        merge_row2 = 'N' + str(row + 1) + ':O' + str(row + 1)
                        sheet.merge_range(merge_row2, amount_qty or "-",data_cell_number_format)
                        sheet.write_row(row,0, data_list_1,data_cell_format)
                    
                    if stock_move_ids.location_dest_id.usage in ('internal', 'transit') and location_dest_id_check:
                        row += 1
                        number += 1

                        amount_qty = amount_qty + qty
                        in_amount = in_amount + qty
                        qty_9 = qty
                        internal_total_qty = internal_total_qty + qty_9

                        data_list_1 = [
                                    str(stock_move_ids.date.strftime('%d-%m-%y')), 
                                    origin or '',
                                    reference or '',
                                    self.get_reference_detail(reference) or '',
                                    customer,
                                    invoice_posted.name or '',
                                    product_uom_id,
                                    "",
                                    location_dest_id or "-", 
                                    ]
                        merge_row = 'J' + str(row + 1) + ':K' + str(row + 1)
                        sheet.merge_range(merge_row, qty_9 or "-",data_cell_number_format)

                        merge_row1 = 'L' + str(row + 1) + ':M' + str(row + 1)
                        sheet.merge_range(merge_row1, "-",data_cell_number_format)

                        merge_row2 = 'N' + str(row + 1) + ':O' + str(row + 1)
                        sheet.merge_range(merge_row2, amount_qty or "-",data_cell_number_format)
                        sheet.write_row(row,0, data_list_1,data_cell_format)

                    amount_total = amount_qty

                in_total = in_total + in_amount
                out_total = out_total + out_amount
            before_total_sum += before_total
        row += 1
        sheet.write(row,7, "TOTAL", grandtotal_cell_format)
        grand_amount_total = grand_amount_total + amount_total 
        merge_row = 'J' + str(row + 1) + ':K' + str(row + 1)
        sheet.merge_range(merge_row, internal_total_qty or "-",data_cell_number_format)

        merge_row1 = 'L' + str(row + 1) + ':M' + str(row + 1)
        sheet.merge_range(merge_row1, transit_total_qty or "-",data_cell_number_format)

        merge_row2 = 'N' + str(row + 1) + ':O' + str(row + 1)
        sheet.merge_range(merge_row2, amount_total or "-",data_cell_number_format)
        row += 1

        data_list = ["",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    ]
        sheet.write_row(row,0, data_list,format_footerC_bold)  

        sheet.write(row,3, "GRAND TOTAL", grandtotal_cell_format)

        merge_row = 'J' + str(row + 1) + ':K' + str(row + 1)
        sheet.merge_range(merge_row, in_total or "-",format_footerC_bold)

        merge_row1 = 'L' + str(row + 1) + ':M' + str(row + 1)
        sheet.merge_range(merge_row1, out_total or "-",format_footerC_bold)

        merge_row2 = 'N' + str(row + 1) + ':O' + str(row + 1)
        sheet.merge_range(merge_row2, grand_amount_total or "-",format_footerC_bold)

        