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

class SOLineSaleXlsx(models.AbstractModel):
    _name = 'report.so_line_sale_xlsx'
    _description = 'report.so_line_sale_xlsx'
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
        if wizard_data.user_id :
            user_ids = wizard_data.user_id
        else:
            orders = self.env['sale.order'].search([('create_date', '<=', date_to), ('create_date', '>=', date_from)])
            user_ids = list(set(map(lambda order: order.user_id, orders)))

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
        report_name = ("sale order line Sales report")
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
        sheet.write(0, 0, 'SPE Open sales lines by พนักงาน',top_cell_format)
        for user_id in user_ids:
            order_line = self.env['sale.order.line'].search([('order_id.user_id', '=', user_id.id),('order_id.create_date', '<=', date_to), ('order_id.create_date', '>=', date_from)])
            if not order_line:
                continue

            sheet.write(row,0, 'Number', head_sub_cell_format_cus)
            sheet.write(row,1, 'Sales Respond', head_sub_cell_format_cus)
            for col in range(2, 27):
                sheet.write(row, col, '', border_format_buttom)
            row +=1
            sheet.write(row,0, user_id.id, data_cell_format_left_cus)
            sheet.write(row,1, user_id.name, data_cell_format_left_cus)

            row +=1
            sheet.write(row,0, 'Ship date', head_sub_cell_format)
            sheet.write(row,1, 'Customer', head_sub_cell_format)
            sheet.write(row,2, 'Name', head_sub_cell_format)
            sheet.write(row,3, 'Sales Order', head_sub_cell_format)
            sheet.write(row,4, 'Item Number', head_sub_cell_format)
            sheet.write(row,5, 'Description', head_sub_cell_format)
            sheet.write(row,6, 'โครงการ', head_sub_cell_format)
            sheet.write(row,7, 'Status', head_sub_cell_format)
            sheet.write(row,8, 'Doc Status', head_sub_cell_format)
            sheet.write(row,9, 'Unit', head_sub_cell_format)
            sheet.write(row,10, 'Unit Price', head_sub_cell_format)
            sheet.write(row,11, 'Discount', head_sub_cell_format)
            sheet.write(row,12, 'Quantity', head_sub_cell_format)
            sheet.write(row,13, 'Sales Spec', head_sub_cell_format)
            sheet.write(row,14, 'Sales Responsible', head_sub_cell_format)
            sheet.write(row,15, 'Sales Taker', head_sub_cell_format)
            sheet.write(row,16, 'Sales pool', head_sub_cell_format)
            sheet.write(row,17, 'PO ลูกค้า', head_sub_cell_format)
            sheet.write(row,18, 'Invoice No.', head_sub_cell_format)
            sheet.write(row,19, 'Spe Invoice No.', head_sub_cell_format)
            sheet.write(row,20, 'Voucher', head_sub_cell_format)
            sheet.write(row,21, 'วันที่ขึ้นบัญชี', head_sub_cell_format)
            sheet.write(row,22, 'Delivery \nremainder', head_sub_cell_format_warp)
            sheet.write(row,23, 'Delivery', head_sub_cell_format)
            sheet.write(row,24, 'Currency', head_sub_cell_format)

            sheet.write(row,25, 'Amount ordered\ncurrency', head_sub_cell_format_warp)
            sheet.write(row,26, 'Amount ordered', head_sub_cell_format)

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
            }

            for col, width in column_widths.items():
                sheet.set_column(col, col, width)

            row += 1
            amount_total = 0.0
            discount_total = 0.0
            unit_price_total = 0.0

            for i, line in enumerate(order_line):
                discount_total += line.dis_price if line.dis_price else 0.0
                amount_total += line.price_total if line.price_total else 0.0
                unit_price_total += line.price_unit if line.price_unit else 0.0
                delivery_remain = line.product_uom_qty - line.qty_delivered
                invoice_lines = ''
                invoice_lines_spe = ''
                invoice_date = ''
                if line.invoice_lines and line.invoice_lines[0]:
                    if line.invoice_lines[0].move_id:
                        invoice_lines = line.invoice_lines[0].move_id.name
                        invoice_lines_spe = line.invoice_lines[0].move_id.form_no
                        invoice_date = line.invoice_lines[0].move_id.invoice_date.strftime('%d/%m/%Y') if line.invoice_lines[0].move_id.invoice_date else ''
                if isinstance(invoice_lines_spe, bool):
                    invoice_lines_spe = ''  # กำหนดเป็นค่าว่างถ้าเป็น boolean 
                default_code = line.product_id.default_code if isinstance(line.product_id.default_code, str) else ''
                so_number = line.order_id.name if isinstance(line.order_id.name, str) else ''
                description = line.name if isinstance(line.name, str) else ''
                so_state = line.order_id.state if isinstance(line.order_id.state, str) else ''
                project_name = line.order_id.project_name.name if line.order_id.project_name else ''
                product_uom = line.product_uom.name if line.product_uom else ''
                sale_spec = line.order_id.sale_spec if line.order_id.sale_spec else ''
                sale_taker = line.order_id.user_sale_agreement.name if line.order_id.user_sale_agreement else ''
                sale_respond = line.order_id.user_id.name if line.order_id.user_id else ''
                customer_po = line.order_id.customer_po if line.order_id.customer_po else ''

                sheet.write_row(row,0, [line.create_date.strftime('%d/%m/%Y')],data_cell_format_left)#รอดูวันส่งดึงจากไหน
                sheet.write_row(row,1, [line.order_id.partner_id.ref],data_cell_format_left)
                sheet.write_row(row,2, [line.order_id.partner_id.name],data_cell_format_left)
                sheet.write_row(row,3, [so_number],data_cell_format_left)
                sheet.write_row(row,4, [default_code],data_cell_format_left)
                sheet.write_row(row,5, [description],data_cell_format_left)
                sheet.write_row(row,6, [project_name],data_cell_format_left) 
                sheet.write_row(row,7, [so_state],data_cell_format_left) #status
                sheet.write_row(row,8, '',data_cell_format_left) #doc status
                sheet.write_row(row,9, [product_uom],data_cell_format)

                sheet.write_row(row,10, [line.price_unit],data_cell_format)
                sheet.write_row(row,11, [line.dis_price],data_cell_format)
                sheet.write_row(row,12, [line.product_uom_qty],data_cell_format)

                sheet.write_row(row,13, [sale_spec],data_cell_format_left)
                sheet.write_row(row,14, [sale_respond],data_cell_format_left)
                sheet.write_row(row,15, [sale_taker],data_cell_format_left)
                sheet.write_row(row,16, '',data_cell_format_left) #sale pool
                sheet.write_row(row,17, [customer_po],data_cell_format_left) 
                sheet.write_row(row,18, [invoice_lines],data_cell_format_left) 
                sheet.write_row(row,19, [invoice_lines_spe],data_cell_format_left) 
                sheet.write_row(row,20, '',data_cell_format_left)#voucher
                sheet.write_row(row,21, [invoice_date] ,data_cell_format_left)

                sheet.write_row(row,22, [delivery_remain],data_cell_format)
                sheet.write_row(row,23, [line.qty_delivered],data_cell_format)
                sheet.write_row(row,24, [line.currency_id.name],data_cell_format_left)
                sheet.write_row(row,25, [line.price_total],data_cell_format)
                sheet.write_row(row,26, [line.price_total],data_cell_format)

                row += 1
            row += 1
            sheet.write_row(row,10, [unit_price_total] ,data_bold_cell_format_number)
            sheet.write_row(row,11, [discount_total],data_bold_cell_format_number)
            sheet.write_row(row,26, [''] ,border_format_buttom)
            row += 1
            sheet.write_row(row,0, ['Total'],data_cell_format_left_bold)
            sheet.write_row(row,26, [amount_total] ,data_bold_cell_format_number)
        
            grand_amount_total += amount_total
            row += 2
        sheet.write_row(f'A{row}', [''] * 27, border_format_buttom)
        sheet.write_row(row,0, ['Grand Total'],data_cell_format_left_bold)
        sheet.write_row(row,26, [grand_amount_total],data_cell_format_line2)
            