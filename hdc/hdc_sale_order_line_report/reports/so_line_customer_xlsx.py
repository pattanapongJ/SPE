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

class SOLineCustomerXlsx(models.AbstractModel):
    _name = 'report.so_line_customer_xlsx'
    _description = 'report.so_line_customer_xlsx'
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

    def generate_xlsx_report(self, workbook, data, wizard_data):
        start_date = wizard_data.from_date
        to_date = wizard_data.to_date
        date_from = wizard_data.from_date
        date_to = wizard_data.to_date
        start_date = start_date.strftime("%Y-%m-%d 00:00:00")
        to_date = to_date.strftime("%Y-%m-%d 23:59:59")
        if wizard_data.partner_id :
            partner_id = wizard_data.partner_id
        else:
            orders = self.env['sale.order'].search([('create_date', '<=', date_to), ('create_date', '>=', date_from)])
            partner_id = list(set(map(lambda order: order.partner_id, orders)))

        top_cell_format = workbook.add_format({
            'bold': True,
            'align': 'left',
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
            'num_format': '#,##0.00',
            'align': 'right',
            'border': False,
        })
        data_cell_format.set_font_size(9)
        data_cell_format.set_align('vcenter')
        data_cell_format.set_font_name('Kanit')

        data_cell_format_line = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'border': False,
            'bottom': 1
        })
        data_cell_format_line.set_font_size(9)
        data_cell_format_line.set_align('vcenter')
        data_cell_format_line.set_font_name('Kanit')

        data_cell_format_line2 = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'bold': True,
            'border': False,
            'bottom': 6
        })
        data_cell_format_line2.set_font_size(9)
        data_cell_format_line2.set_align('vcenter')
        data_cell_format_line2.set_font_name('Kanit')

        data_cell_format_left = workbook.add_format({
            'align': 'left',
            'border': False,
        })
        data_cell_format_left.set_font_size(9)
        data_cell_format_left.set_align('vcenter')
        data_cell_format_left.set_font_name('Kanit')

        data_cell_format_left_bold = workbook.add_format({
            'bold': True,
            'align': 'left',
            'border': False,
        })
        data_cell_format_left_bold.set_font_size(9)
        data_cell_format_left_bold.set_align('vcenter')
        data_cell_format_left_bold.set_font_name('Kanit')

        data_cell_format_left_cus = workbook.add_format({
            'align': 'left',
            'border': False,
        })
        data_cell_format_left_cus.set_font_size(9)
        data_cell_format_left_cus.set_align('vcenter')
        data_cell_format_left_cus.set_font_name('Kanit')

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
            'align': 'left',
            'border': True,
            # 'bg_color': '#92D050'
        })
        head_cell_format.set_font_size(9)
        head_cell_format.set_align('vleft')
        head_cell_format.set_font_name('Kanit')
        head_cell_format_no_color = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': True,
        })
        head_cell_format_no_color.set_font_size(9)
        head_cell_format_no_color.set_align('vcenter')
        head_cell_format_no_color.set_font_name('Kanit')

        border_format_buttom = workbook.add_format({
            'bottom': 1,  # เส้นขอบล่างบาง
        })

        head_sub_cell_format = workbook.add_format({
            'align': 'center',
            'bold': True,
            'top': 1, 
        })
        head_sub_cell_format.set_font_size(9)
        head_sub_cell_format.set_align('vcenter')
        head_sub_cell_format.set_font_name('Kanit')

        head_sub_cell_format_warp = workbook.add_format({
            'align': 'center',
            'bold': True,
            'top': 1,
        })
        head_sub_cell_format_warp.set_font_size(9)
        head_sub_cell_format_warp.set_align('vcenter')
        head_sub_cell_format_warp.set_font_name('Kanit')
        head_sub_cell_format_warp.set_text_wrap()

        head_sub_cell_format_cus = workbook.add_format({
            'align': 'center',
            'bold': True,
            'bottom': 1,
        })
        head_sub_cell_format_cus.set_font_size(9)
        head_sub_cell_format_cus.set_align('vcenter')
        head_sub_cell_format_cus.set_font_name('Kanit')
        head_sub_cell_format_cus.set_bottom(1)
        
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
        report_name = ("sale order line Customer report")
        sheet = workbook.add_worksheet(report_name)

        current_dateTime = datetime.now()
        sheet.write(0, 8, current_dateTime.strftime('%d/%m/%y'),datetime_format)
        sheet.write(1, 8, current_dateTime.strftime('%I:%M %p'),datetime_format)
        
        sheet.set_row(0, 20)
        sheet.set_row(1, 15)
        sheet.set_row(2, 15)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 3, 20)
        sheet.set_column(4, 4, 40)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 8, 15)
        sheet.set_column(9, 12, 15)
        row = 5
        grand_amount_total = 0.0
        grand_qty_total = 0.0
        grand_delivery_qty_total = 0.0
        grand_delivery_remain_qty_total = 0.0
        sheet.write(0, 0, 'SPE Open sales line by customer',top_cell_format)
        for customer in partner_id:
            order_line = self.env['sale.order.line'].search([('order_id.partner_id', '=', customer.id),('order_id.create_date', '<=', date_to), ('order_id.create_date', '>=', date_from)])
            if not order_line:
                continue
            sheet.write(row,0, 'Customer', head_sub_cell_format_cus)
            for col in range(1, 32):  # เริ่มจากคอลัมน์ที่ 1 (B) ถึงคอลัมน์ที่ 31 (AF)
                sheet.write(row, col, '', border_format_buttom)
            row +=1
            sheet.write(row,0, customer.ref, data_cell_format_left_cus)
            sheet.write(row,2, customer.name, data_cell_format_left_cus)

            row +=1
            sheet.write(row,0, 'Sales Order', head_sub_cell_format)
            sheet.write(row,1, 'Item Number', head_sub_cell_format)
            sheet.write(row,2, 'Item Name', head_sub_cell_format)
            sheet.write(row,3, 'External Item', head_sub_cell_format)
            sheet.write(row,4, 'Barcode', head_sub_cell_format)
            sheet.write(row,5, 'SO Status', head_sub_cell_format)
            sheet.write(row,6, 'Doc \nStatus', head_sub_cell_format_warp)
            sheet.write(row,7, 'Line \nStatus', head_sub_cell_format_warp)
            sheet.write(row,8, 'Unit', head_sub_cell_format)
            sheet.write(row,9, 'Sale Price', head_sub_cell_format)
            sheet.write(row,10, 'Unit Price', head_sub_cell_format)
            sheet.write(row,11, 'Discount', head_sub_cell_format)
            sheet.write(row,12, 'Amount ordered', head_sub_cell_format)
            sheet.write(row,13, 'Quantity', head_sub_cell_format)
            sheet.write(row,14, 'Delivery', head_sub_cell_format)
            sheet.write(row,15, 'Delivery \nremainder', head_sub_cell_format_warp)
            sheet.write(row,16, 'Sale Price', head_sub_cell_format)
            sheet.write(row,17, 'PO สินค้าค้างรับ', head_sub_cell_format)
            sheet.write(row,18, 'PO Header \nETA Date', head_sub_cell_format_warp)
            sheet.write(row,19, 'PO Receipt \nWH DAte', head_sub_cell_format_warp)
            sheet.write(row,20, 'สต๊อครวม', head_sub_cell_format)
            sheet.write(row,21, 'Invoice No.', head_sub_cell_format)
            sheet.write(row,22, 'Spe Invoice No.', head_sub_cell_format)
            sheet.write(row,23, 'Sales Spec', head_sub_cell_format)
            sheet.write(row,24, 'Sales Responsible', head_sub_cell_format)
            sheet.write(row,25, 'Sales Taker', head_sub_cell_format)
            sheet.write(row,26, 'pool', head_sub_cell_format)
            sheet.write(row,27, 'PO ลูกค้า', head_sub_cell_format)
            sheet.write(row,28, 'โครงการ', head_sub_cell_format)
            sheet.write(row,29, 'Picking Note', head_sub_cell_format)
            sheet.write(row,30, 'Line Remark', head_sub_cell_format)
            sheet.write(row,31, 'CreateDate', head_sub_cell_format)

            column_widths = {
                0: 15,  # A
                1: 20,  # B
                2: 45,  # C
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
                20: 15,  # U
                21: 15,  # V
                22: 15,  # W
                23: 15,  # X
                24: 20,  # Y
                25: 20,  # Z
                26: 15, # AA
                27: 15, # AB
                28: 15, # AC
                29: 15, # AD
                30: 15, # AE
                31: 15, # AF
            }

            for col, width in column_widths.items():
                sheet.set_column(col, col, width)

            row += 1
            amount_total = 0.0
            discount_total = 0.0
            qty_total = 0.0
            delivery_qty_total = 0.0
            delivery_remain_qty_total = 0.0

            for i, line in enumerate(order_line):
                discount_total += line.dis_price if line.dis_price else 0.0
                amount_total += line.price_total if line.price_total else 0.0
                qty_total += line.product_uom_qty if line.product_uom_qty else 0.0
                delivery_qty_total += line.qty_delivered if line.qty_delivered else 0.0
                delivery_remain = line.product_uom_qty - line.qty_delivered
                delivery_remain_qty_total += delivery_remain
                invoice_lines = ''
                invoice_lines_spe = ''
                if line.invoice_lines and line.invoice_lines[0]:
                    if line.invoice_lines[0].move_id:
                        invoice_lines = line.invoice_lines[0].move_id.name
                        invoice_lines_spe = line.invoice_lines[0].move_id.form_no
                if isinstance(invoice_lines_spe, bool):
                    invoice_lines_spe = ''  # กำหนดเป็นค่าว่างถ้าเป็น boolean 
                default_code = line.product_id.default_code if isinstance(line.product_id.default_code, str) else ''
                so_number = line.order_id.name if isinstance(line.order_id.name, str) else ''
                product_name = line.product_id.name if isinstance(line.product_id.name, str) else ''
                so_state = line.order_id.state if isinstance(line.order_id.state, str) else ''
                barcode = line.barcode if isinstance(line.barcode, str) else ''
                sheet.write_row(row,0, [so_number],data_cell_format_left)
                sheet.write_row(row,1, [default_code],data_cell_format_left)
                sheet.write_row(row,2, [product_name],data_cell_format_left)
                sheet.write_row(row,3, '',data_cell_format_left)
                sheet.write_row(row,4, [barcode],data_cell_format_left)
                sheet.write_row(row,5, [so_state],data_cell_format_left)
                sheet.write_row(row,6, '',data_cell_format_left)
                sheet.write_row(row,7, '',data_cell_format_left)
                sheet.write_row(row,8, [line.product_uom.name],data_cell_format_left)
                sheet.write_row(row,9, [line.product_id.lst_price],data_cell_format)
                sheet.write_row(row,10, [line.price_unit],data_cell_format)
                sheet.write_row(row,11, [line.dis_price],data_cell_format)
                sheet.write_row(row,12, [line.price_total],data_cell_format)
                sheet.write_row(row,13, [line.product_uom_qty],data_cell_format)
                sheet.write_row(row,14, [line.qty_delivered],data_cell_format)
                sheet.write_row(row,15, [delivery_remain],data_cell_format)
                sheet.write_row(row,16, '',data_cell_format_left) #sale price
                sheet.write_row(row,17, '',data_cell_format_left) #PO สินค้าค้างรับ
                sheet.write_row(row,18, '',data_cell_format_left) #PO Header / ETA Date
                sheet.write_row(row,19, '',data_cell_format_left) #PO Receipt / WH DAte
                sheet.write_row(row,20, [line.product_id.qty_available],data_cell_format)
                sheet.write_row(row,21, [invoice_lines] ,data_cell_format_left)
                sheet.write_row(row,22, [invoice_lines_spe],data_cell_format_left)
                sheet.write_row(row, 23, [line.order_id.sale_spec.name if line.order_id.sale_spec else ''], data_cell_format_left)
                sheet.write_row(row,24, [line.order_id.user_id.name],data_cell_format_left)
                sheet.write_row(row,25, [line.order_id.user_sale_agreement.name],data_cell_format_left)
                sheet.write_row(row,26, '',data_cell_format_left) #pool
                sheet.write_row(row,27, line.order_id.customer_po if line.order_id.customer_po else '',data_cell_format_left)
                sheet.write_row(row,28, line.order_id.project_name.project_name if line.order_id.project_name else '',data_cell_format_left)
                sheet.write_row(row,29, '',data_cell_format_left) #picking note
                sheet.write_row(row,30, '',data_cell_format_left) #line remark
                sheet.write_row(row,31, [line.create_date.strftime('%d/%m/%Y')],data_cell_format_left)
                row += 1
            row += 1
            sheet.write_row(row,11, [discount_total],data_cell_format)
            sheet.write_row(row,12, [amount_total] ,data_cell_format_line)
            sheet.write_row(row,13, [qty_total] ,data_cell_format_line)
            sheet.write_row(row,14, [delivery_qty_total] ,data_cell_format_line)
            sheet.write_row(row,15, [delivery_remain_qty_total] ,data_cell_format_line)
            row += 1
            sheet.write_row(row,0, ['Total'],data_cell_format_left_bold)
            sheet.write_row(row,12, [amount_total] ,data_bold_cell_format_number)
            sheet.write_row(row,13, [qty_total] ,data_bold_cell_format_number)
            sheet.write_row(row,14, [delivery_qty_total] ,data_bold_cell_format_number)
            sheet.write_row(row,15, [delivery_remain_qty_total] ,data_bold_cell_format_number)
        
            grand_amount_total += amount_total
            grand_qty_total += qty_total
            grand_delivery_qty_total += delivery_qty_total
            grand_delivery_remain_qty_total += delivery_remain_qty_total
            row += 2
        sheet.write_row(f'A{row}', [''] * 32, border_format_buttom)
        sheet.write_row(row,0, ['Grand Total'],data_cell_format_left_bold)
        sheet.write_row(row,12, [grand_amount_total],data_cell_format_line2)
        sheet.write_row(row,13, [grand_qty_total] ,data_cell_format_line2)
        sheet.write_row(row,14, [grand_delivery_qty_total] ,data_cell_format_line2)
        sheet.write_row(row,15, [grand_delivery_remain_qty_total] ,data_cell_format_line2)
            