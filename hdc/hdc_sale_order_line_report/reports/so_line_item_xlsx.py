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

class SOLineItemXlsx(models.AbstractModel):
    _name = 'report.so_line_item_xlsx'
    _description = 'report.so_line_item_xlsx'
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
        if wizard_data.product_id :
            product_ids = wizard_data.product_id
        else:
            orders = self.env['sale.order.line'].search([('order_id.create_date', '<=', date_to), ('order_id.create_date', '>=', date_from)])
            product_ids = list(set(map(lambda order: order.product_id, orders)))

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
        report_name = ("sales order lines by Item report")
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
        sheet.write(0, 0, 'SPE Open sales lines by Item',top_cell_format)
        for item in product_ids:
            order_line = self.env['sale.order.line'].search([('product_id', '=', item.id),('order_id.create_date', '<=', date_to), ('order_id.create_date', '>=', date_from)])
            if not order_line:
                continue
            item_number = item.default_code if isinstance(item.default_code, str) else ''
            sheet.write(row,0, 'Item Number', head_sub_cell_format_cus)
            sheet.write(row,1, '', border_format_buttom)
            sheet.write(row,2, 'Description', head_sub_cell_format_cus)
            for col in range(3, 12): 
                sheet.write(row, col, '', border_format_buttom)
            row +=1
            sheet.write(row,0, item_number, data_cell_format_left_cus)
            sheet.write(row,1, item.name, data_cell_format_left_cus)

            row +=1
            sheet.write(row,0, 'Ship date', head_sub_cell_format)
            sheet.write(row,1, 'Sales Order', head_sub_cell_format)
            sheet.write(row,2, 'Picking Note', head_sub_cell_format)
            sheet.write(row,3, 'Customer', head_sub_cell_format)
            sheet.write(row,4, 'Doc Status', head_sub_cell_format)
            sheet.write(row,5, 'Unit', head_sub_cell_format)
            sheet.write(row,6, 'Quantity', head_sub_cell_format)
            sheet.write(row,7, 'Unit Price', head_sub_cell_format)
            sheet.write(row,8, 'Delivery \nremainder', head_sub_cell_format_warp)
            sheet.write(row,9, 'Currency', head_sub_cell_format)
            sheet.write(row,10, 'Amount\nordered\ncurrency', head_sub_cell_format_warp)
            sheet.write(row,11, 'Amount ordered', head_sub_cell_format)

            column_widths = {
                0: 15,  # A
                1: 20,  # B
                2: 15,  # C
                3: 15,  # D
                4: 15,  # E
                5: 15,  # F
                6: 15,  # G
                7: 15,  # H
                8: 15,  # I
                9: 15,  # J
                10: 20,  # K
                11: 20,  # L
            }

            for col, width in column_widths.items():
                sheet.set_column(col, col, width)

            row += 1
            amount_total = 0.0

            for i, line in enumerate(order_line):
                amount_total += line.price_total if line.price_total else 0.0
                delivery_remain = line.product_uom_qty - line.qty_delivered
                
                so_number = line.order_id.name if isinstance(line.order_id.name, str) else ''
                so_state = line.order_id.state if isinstance(line.order_id.state, str) else ''
                product_uom = line.product_uom.name if line.product_uom else ''

                sheet.write_row(row,0, [line.create_date.strftime('%d/%m/%Y')],data_cell_format_left)#รอดูวันส่งดึงจากไหน
                sheet.write_row(row,1, [so_number],data_cell_format_left)
                sheet.write_row(row,2, '',data_cell_format_left)
                sheet.write_row(row,3, [line.order_id.partner_id.ref],data_cell_format_left)
                sheet.write_row(row,4, [so_state],data_cell_format_left) #doc status
                sheet.write_row(row,5, [product_uom],data_cell_format_left)
                sheet.write_row(row,6, [line.product_uom_qty],data_cell_format) 
                sheet.write_row(row,7, [line.price_unit],data_cell_format) #status
                sheet.write_row(row,8, [delivery_remain],data_cell_format) #doc status
                sheet.write_row(row,9, [line.currency_id.name],data_cell_format_left)

                sheet.write_row(row,10, [line.price_total],data_cell_format)
                sheet.write_row(row,11, [line.price_total],data_cell_format)

                row += 1
            sheet.write_row(row,11, [''] ,border_format_buttom)
            row += 1
            sheet.write_row(row,0, ['Total'],data_cell_format_left_bold)
            sheet.write_row(row,11, [amount_total] ,data_bold_cell_format_number)
        
            row += 2
            