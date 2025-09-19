# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
import pytz
import datetime
from datetime import datetime, date, time
from decimal import Decimal, ROUND_HALF_UP
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError, except_orm
import os

import io
import base64
from PIL import Image
from dateutil.relativedelta import relativedelta

class ExportAdjustmentManualLinexlsx(models.AbstractModel):
    _name = 'report.export_adjustment_manual_line_report_xlsx'
    _description = 'report.export_adjustment_manual_line_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        valuation_adjustment_manual_lines = partners.valuation_adjustment_manual_lines
        # format
        top_cell_format = workbook.add_format({
            'bold': True,
            'align': 'left',
        })
        top_cell_format.set_font_size(7)
        top_cell_format.set_align('vcenter')
        top_cell_format.set_font_name('Kanit')
        head_top_cell_format = workbook.add_format({
            'align': 'left',
            'border': True,
            'text_wrap': True,
        })
        head_top_cell_format.set_font_size(7)
        head_top_cell_format.set_align('vleft')
        head_top_cell_format.set_font_name('Kanit')

        data_cell_format = workbook.add_format({
            'align': 'center',
            'border': True,
        })
        data_cell_format.set_font_size(7)
        data_cell_format.set_align('vcenter')
        data_cell_format.set_font_name('Kanit')

        data_cell_format_left = workbook.add_format({
            'align': 'left',
            'border': True,
        })
        data_cell_format_left.set_font_size(7)
        data_cell_format_left.set_align('vcenter')
        data_cell_format_left.set_font_name('Kanit')

        data_cell_format_right = workbook.add_format({
            'align': 'right',
            'border': True,
        })
        data_cell_format_right.set_font_size(7)
        data_cell_format_right.set_align('vcenter')
        data_cell_format_right.set_font_name('Kanit')
        data_cell_number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'border': True,
        })
        data_cell_number_format.set_font_size(7)
        data_cell_number_format.set_align('vcenter')
        data_cell_number_format.set_font_name('Kanit')

        head_cell_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': True,
            'bg_color': '#FF9898'
        })
        head_cell_format.set_font_size(7)
        head_cell_format.set_align('vcenter')
        head_cell_format.set_font_name('Kanit')

        head_cell_format_edit = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': True,
            'bg_color': '#92D050'
        })
        head_cell_format_edit.set_font_size(7)
        head_cell_format_edit.set_align('vcenter')
        head_cell_format_edit.set_font_name('Kanit')

        head_cell_format_up = workbook.add_format({
            'bold': True,
            'align': 'center',
            'top': True,
            'right': True,
            'left': True,
            'bg_color': '#FF9898'
        })
        head_cell_format_up.set_font_size(7)
        head_cell_format_up.set_align('vcenter')
        head_cell_format_up.set_font_name('Kanit')

        head_cell_format_up_edit = workbook.add_format({
            'bold': True,
            'align': 'center',
            'top': True,
            'right': True,
            'left': True,
            'bg_color': '#92D050'
        })
        head_cell_format_up_edit.set_font_size(7)
        head_cell_format_up_edit.set_align('vcenter')
        head_cell_format_up_edit.set_font_name('Kanit')

        head_cell_format_down = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bottom': True,
            'right': True,
            'left': True,
            'bg_color': '#FF9898'
        })
        head_cell_format_down.set_font_size(7)
        head_cell_format_down.set_align('vcenter')
        head_cell_format_down.set_font_name('Kanit')

        head_cell_format_down_edit = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bottom': True,
            'right': True,
            'left': True,
            'bg_color': '#92D050'
        })
        head_cell_format_down_edit.set_font_size(7)
        head_cell_format_down_edit.set_align('vcenter')
        head_cell_format_down_edit.set_font_name('Kanit')

        head_cell_format_no_color = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': True,
        })
        head_cell_format_no_color.set_font_size(7)
        head_cell_format_no_color.set_align('vcenter')
        head_cell_format_no_color.set_font_name('Kanit')

        head_sub_cell_format = workbook.add_format({
            'align': 'center',
            'border': True,
        })
        head_sub_cell_format.set_font_size(7)
        head_sub_cell_format.set_align('vcenter')
        head_sub_cell_format.set_font_name('Kanit')
        data_bold_cell_format = workbook.add_format({
            'bold': True,
            'align': 'left',
        })
        data_bold_cell_format.set_font_size(7)
        data_bold_cell_format.set_align('vcenter')
        data_bold_cell_format.set_font_name('Kanit')

        data_bold_cell_format_number = workbook.add_format({
            'num_format': '#,##0.00',
            'bold': True,
            'align': 'right',
        })
        data_bold_cell_format_number.set_font_size(7)
        data_bold_cell_format_number.set_align('vcenter')
        data_bold_cell_format_number.set_font_name('Kanit')

        format_footerC_bold = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right', 
            'top': True
        })
        format_footerC_bold.set_font_size(7)
        format_footerC_bold.set_align('vcenter')
        format_footerC_bold.set_font_name('Kanit')

        datetime_format = workbook.add_format({'align': 'right'})
        datetime_format.set_font_size(7)
        datetime_format.set_align('vcenter')
        datetime_format.set_font_name('Kanit')

        # report name
        report_name = ("Landed Cost - Valuation Adjustments Manual - " + partners.name)
        sheet = workbook.add_worksheet(report_name)
        sheet.set_paper(9)  # A4
        sheet.set_landscape()
        sheet.set_margins(left=0.25, right=0.25, top=0.55, bottom=0.3)
                
        sheet.set_row(0, 20)
        sheet.set_row(1, 15)
        sheet.set_row(2, 15)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 3, 20)
        sheet.set_column(4, 4, 40)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 8, 15)
        sheet.set_column(9, 12, 15)

        row = 0
        sheet.set_row(row, 15)
        sheet.set_row(row+1, 15)
        sheet.write(row,0, 'ID', head_cell_format)
        sheet.write(row,1, 'Product Name', head_cell_format)
        sheet.write(row,2, 'Item', head_cell_format)
        sheet.write(row,3, 'Free Product', head_cell_format_edit)
        sheet.write(row,4, 'No Calculate Landed', head_cell_format_edit)
        sheet.write(row,5, 'Receipt/RL', head_cell_format)
        sheet.write(row,6, 'Quantity', head_cell_format_edit)
        sheet.write(row,7, 'Unit', head_cell_format)
        sheet.write(row,8, 'Unit Price', head_cell_format)
        sheet.write(row,9, 'Amount', head_cell_format_edit)
        sheet.write(row,10, 'Discount', head_cell_format_edit)
        sheet.write(row,11, 'Rate USD', head_cell_format_edit)
        sheet.write(row,12, 'ราคาของ(บาท)', head_cell_format_edit)
        sheet.write(row,13, 'ของฟรี', head_cell_format_edit)
        sheet.write(row,14, 'ราคาขสินค้าทั้งสิ้น', head_cell_format_edit)
        sheet.write(row,15, 'Duty%', head_cell_format_edit)
        sheet.write(row,16, 'ค่าอากร(เฉลี่ย)', head_cell_format_edit)
        sheet.write(row,17, 'ค่าอากร(เฉลี่ย)2', head_cell_format_edit)
        sheet.write(row,18, 'ตัวเฉลี่ยอากร', head_cell_format_edit)
        sheet.write(row,19, 'เฉลี่ย SH', head_cell_format_edit)
        sheet.write(row,20, 'เฉลี่ย DO', head_cell_format_edit)
        sheet.write(row,21, 'เฉลี่ย INS', head_cell_format_edit)
        sheet.write(row,22, 'รวมอากร +SH', head_cell_format_edit)
        sheet.write(row,23, 'Original Value', head_cell_format)
        sheet.write(row,24, 'Additional Landed Cost', head_cell_format_edit)
        sheet.write(row,25, 'New Value', head_cell_format)


        column_widths = {
            0: 10,  # A
            1: 15,  # B
            2: 30,  # C
            3: 15,  # D
            4: 15,  # E
            5: 15,  # F
            6: 15,  # G
            7: 15,  # H
            8: 15,  # I
            9: 15,  # J
            10: 10,  # K
            11: 10,  # L
            12: 15,  # M
            13: 15,  # N
            14: 15,  # O
            15: 15,  # P
            16: 15, # Q
            17: 15, # R
            18: 15, # S
            19: 15, # T
            20: 15, # u
            21: 15, # v
            22: 15, # x
            23: 15, # y
            24: 15, # z
            25: 15, # aa
        }
        
        for col, width in column_widths.items():
            sheet.set_column(col, col, width)

        row = 0
        for item in valuation_adjustment_manual_lines:
            row += 1
            data_list_1 = [ 
                            item.product_id.name or '',
                            item.item_code or '',
                            item.free_product,
                            item.no_cal_landed_cost,
                            item.receipt_name or '',
                            item.quantity or '',
                            item.product_uom.name or '',
                            item.price_unit or '',
                            item.amount_price or '',
                            item.discount or '',
                            item.rate_usd or '',
                            item.price_item or '',
                            item.free_item or '',
                            item.amount_item or '',
                            item.duty or '',
                            item.duty_avg or '',
                            item.duty_avg2 or '',
                            item.duty_avg_total or '',
                            item.sh_avg or '',
                            item.do_avg or '',
                            item.ins_avg or '',
                            item.total_duty_sh or '',
                            item.former_cost or '',
                            item.landed_value or '',
                            item.final_cost or '',
                        ]

            sheet.write(row,0, item.id or '', data_cell_format)
            sheet.write_row(row,1, data_list_1,data_cell_format_left)

                    
    
                    