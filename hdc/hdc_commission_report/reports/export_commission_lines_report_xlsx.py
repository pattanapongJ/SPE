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

class ExportCommissionLinesXlsx(models.AbstractModel):
    _name = 'report.export_commission_lines_report_xlsx'
    _description = 'report.export_commission_line_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        commission_sold_out_lines = partners.commission_sold_out_lines
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
        report_name = ("Commission Sold Out Lines " + partners.name)
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
        sheet.write(row,0, 'ID', head_cell_format_up)
        sheet.write(row+1,0, '', head_cell_format_down)
        sheet.write(row,1, 'รหัส/รายชื่อลูกค้า(จากระบบ odoo)', head_cell_format_up)
        sheet.write(row+1,1, '', head_cell_format_down)
        sheet.write(row,2, 'นิติ', head_cell_format_up)
        sheet.write(row+1,2, '', head_cell_format_down)
        merge_row = 'D' + str(row + 1) + ':E' + str(row + 1)
        sheet.merge_range(merge_row, 'Sold Out Value', head_cell_format_edit)
        sheet.write(row+1,3, 'มูลค่า(รวมภาษี)', head_cell_format_down_edit)
        sheet.write(row+1,4, 'มูลค่า(ก่อนภาษี)', head_cell_format_down_edit)
        merge_row = 'F' + str(row + 1) + ':G' + str(row + 1)
        sheet.merge_range(merge_row, 'Expenses', head_cell_format_edit)
        sheet.write(row+1,5, 'Rate', head_cell_format_down_edit)
        sheet.write(row+1,6, 'Value', head_cell_format_down_edit)
        sheet.write(row,7, 'CN (Odoo)', head_cell_format_up)
        sheet.write(row+1,7, 'CN/ก่อนภาษี', head_cell_format_down)
        sheet.write(row,8, 'Cal.COM Value', head_cell_format_up_edit)
        sheet.write(row+1,8, '', head_cell_format_down_edit)
        merge_row = 'J' + str(row + 1) + ':K' + str(row + 1)
        sheet.merge_range(merge_row, 'Commission', head_cell_format_edit)
        sheet.write(row+1,9, 'Rate', head_cell_format_down_edit)
        sheet.write(row+1,10, 'Value', head_cell_format_down_edit)
        sheet.write(row,11, 'หัก Commission', head_cell_format_up_edit)
        sheet.write(row+1,11, '', head_cell_format_down_edit)

        column_widths = {
            0: 6,  # A
            1: 20,  # B
            2: 20,  # C
            3: 12,  # D
            4: 12,  # E
            5: 6,  # F
            6: 10,  # G
            7: 10,  # H
            8: 10,  # I
            9: 6,  # J
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
        }
        
        for col, width in column_widths.items():
            sheet.set_column(col, col, width)

        row = 1
        for item in commission_sold_out_lines:
            row += 1
            data_list_1 = [ item.partner_id.name or '',
                            item.company_id.name or '',]
                            
            data_list_1_2 = [ item.expenses_rate or '',
                            '',
                            '',
                            '',
                            item.commission_rate or '',
                            '',
                            '',
                            ]
            sheet.write(row,0, item.id or '', data_cell_format)
            sheet.write_row(row,1, data_list_1,data_cell_format_left)
            sheet.write_row(row,5, data_list_1_2,data_cell_format_right)
            data_list_2 = [ item.sold_out_amount_tax or '',
                            item.sold_out_amount_untax or '',]
            data_list_3 = [ item.expenses_value or '',
                            item.total_amount_untax_cn or '',
                            item.cal_com_value or '',]
            data_list_4 = [ item.commission_value or '',
                            item.deduct_commission or '',]
            sheet.write_row(row,3, data_list_2,data_cell_number_format)
            sheet.write_row(row,6, data_list_3,data_cell_number_format)
            sheet.write_row(row,10, data_list_4,data_cell_number_format)

                    
    
                    