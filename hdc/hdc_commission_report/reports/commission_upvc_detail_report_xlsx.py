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

class CommissionUpvcDetailXlsx(models.AbstractModel):
    _name = 'report.commission_upvc_detail_report_xlsx'
    _description = 'report.commission_upvc_detail_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):

        settle_commissions_id = partners.settle_commissions_id
        payment_lines = settle_commissions_id.payment_lines
        commission_date = settle_commissions_id.commission_date
        receipted_date_form = settle_commissions_id.receipted_date_form
        receipted_date_to = settle_commissions_id.receipted_date_to
        report_config = partners.commission_report_configuration_id
        team_id = settle_commissions_id.team_id
        commission_types = []
        for report_config_line in report_config.commission_report_configuration_line:
            commission_types.append(report_config_line.commission_type)
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
        })
        data_cell_format.set_font_size(6)
        data_cell_format.set_align('vcenter')
        data_cell_format.set_font_name('Kanit')

        data_cell_format_left = workbook.add_format({
            'align': 'left',
        })
        data_cell_format_left.set_font_size(6)
        data_cell_format_left.set_align('vcenter')
        data_cell_format_left.set_font_name('Kanit')

        data_cell_format_right = workbook.add_format({
            'align': 'right',
        })
        data_cell_format_right.set_font_size(6)
        data_cell_format_right.set_align('vcenter')
        data_cell_format_right.set_font_name('Kanit')

        data_cell_number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
        })
        data_cell_number_format.set_font_size(6)
        data_cell_number_format.set_align('vcenter')
        data_cell_number_format.set_font_name('Kanit')

        data_cell_number_format_sum = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'top': True,
            'bottom': True,
        })
        data_cell_number_format_sum.set_font_size(6)
        data_cell_number_format_sum.set_align('vcenter')
        data_cell_number_format_sum.set_font_name('Kanit')

        head_cell_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': True,
            'bg_color': '#92D050'
        })
        head_cell_format.set_font_size(7)
        head_cell_format.set_align('vcenter')
        head_cell_format.set_font_name('Kanit')

        head_cell_format_up = workbook.add_format({
            'bold': True,
            'align': 'center',
            'top': True,
            'right': True,
            'left': True,
            'bg_color': '#92D050'
        })
        head_cell_format_up.set_font_size(7)
        head_cell_format_up.set_align('vcenter')
        head_cell_format_up.set_font_name('Kanit')

        head_cell_format_mid = workbook.add_format({
            'bold': True,
            'align': 'center',
            'right': True,
            'left': True,
            'bg_color': '#92D050'
        })
        head_cell_format_mid.set_font_size(7)
        head_cell_format_mid.set_align('vcenter')
        head_cell_format_mid.set_font_name('Kanit')

        head_cell_format_down = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bottom': True,
            'right': True,
            'left': True,
            'bg_color': '#92D050'
        })
        head_cell_format_down.set_font_size(7)
        head_cell_format_down.set_align('vcenter')
        head_cell_format_down.set_font_name('Kanit')

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
        report_name = (report_config.name)
        sheet = workbook.add_worksheet(report_name)
        sheet.set_paper(9)  # A4
        sheet.set_landscape()
        sheet.set_margins(left=0.25, right=0.25, top=0.55, bottom=0.3)

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
                
        sheet.set_row(0, 20)
        sheet.set_row(1, 15)
        sheet.set_row(2, 15)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 3, 20)
        sheet.set_column(4, 4, 40)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 8, 15)
        sheet.set_column(9, 12, 15)

        if commission_date:
            day_commission_date = str(commission_date).split('-')[2]
            month_commission_date = str(commission_date).split('-')[1]
            year_commission_date = str(commission_date).split('-')[0]
            if month_commission_date:
                if int(month_commission_date) == 1:
                    text_month_commission_date = 'มกราคม'
                if int(month_commission_date) == 2:
                    text_month_commission_date = 'กุมภาพันธ์'
                if int(month_commission_date) == 3:
                    text_month_commission_date = 'มีนาคม'
                if int(month_commission_date) == 4:
                    text_month_commission_date = 'เมษายน'
                if int(month_commission_date) == 5:
                    text_month_commission_date = 'พฤษภาคม'
                if int(month_commission_date) == 6:
                    text_month_commission_date = 'มิถุนายน'
                if int(month_commission_date) == 7:
                    text_month_commission_date = 'กรกฎาคม'
                if int(month_commission_date) == 8:
                    text_month_commission_date = 'สิงหาคม'
                if int(month_commission_date) == 9:
                    text_month_commission_date = 'กันยายน'
                if int(month_commission_date) == 10:
                    text_month_commission_date = 'ตุลาคม'
                if int(month_commission_date) == 11:
                    text_month_commission_date = 'พฤศจิกายน'
                if int(month_commission_date) == 12:
                    text_month_commission_date = 'ธันวาคม'
            if year_commission_date:
                year_commission_date = int(year_commission_date) + 543

        sheet.merge_range('C2:E2', 'คอมมิชชั่น เดือน' + ' ' + str(text_month_commission_date) + ' ' + str(year_commission_date), top_cell_format)
        sheet.merge_range('C3:E3', 'ทีม' + team_id.name, top_cell_format)

        if receipted_date_form:
            day_receipted_date_form = str(receipted_date_form).split('-')[2]
            month_receipted_date_form = str(receipted_date_form).split('-')[1]
            year_receipted_date_form = str(receipted_date_form).split('-')[0]
            if year_receipted_date_form:
                year_receipted_date_form = int(year_receipted_date_form) + 543

        if receipted_date_to:
            day_receipted_date_to = str(receipted_date_to).split('-')[2]
            month_receipted_date_to = str(receipted_date_to).split('-')[1]
            year_receipted_date_to = str(receipted_date_to).split('-')[0]
            if year_receipted_date_to:
                year_receipted_date_to = int(year_receipted_date_to) + 543
        
        header1 = '&R&"Kanit,Regular"&9Page &P of &N' 
        sheet.set_header(header1,)

        sheet.merge_range('F2:G2', '( รับชำระ' + ' ' + str(day_receipted_date_form) + '/' + str(month_receipted_date_form) + '/' + str(year_receipted_date_form) + ' ถึง ' + str(day_receipted_date_to) + '/' + str(month_receipted_date_to) + '/' + str(year_receipted_date_to) + ' )', top_cell_format)
        
        row = 3
        sheet.set_row(row, 15)
        sheet.set_row(row+1, 15)

        sheet.write(row,0, 'วันที่คิด', head_cell_format_up)
        sheet.write(row+1,0, 'commission', head_cell_format_mid)
        sheet.write(row+2,0, '', head_cell_format_down)

        sheet.write(row,1, 'วันที่', head_cell_format_up)
        sheet.write(row+1,1, 'รับชำระ', head_cell_format_mid)
        sheet.write(row+2,1, '', head_cell_format_down)

        sheet.write(row,2, 'Invoice Date', head_cell_format_up)
        sheet.write(row+1,2, '', head_cell_format_mid)
        sheet.write(row+2,2, '', head_cell_format_down)

        sheet.write(row,3, 'SPE Invoice no.', head_cell_format_up)
        sheet.write(row+1,3, '', head_cell_format_mid)
        sheet.write(row+2,3, '', head_cell_format_down)

        sheet.write(row,4, 'เลขที่เอกสาร', head_cell_format_up)
        sheet.write(row+1,4, 'รับชำระของ', head_cell_format_mid)
        sheet.write(row+2,4, 'ระบบ odoo', head_cell_format_down)

        sheet.write(row,5, 'ชื่อลูกค้า', head_cell_format_up)
        sheet.write(row+1,5, '', head_cell_format_mid)
        sheet.write(row+2,5, '', head_cell_format_down)

        sheet.write(row,6, 'รายการสินค้า', head_cell_format_up)
        sheet.write(row+1,6, '', head_cell_format_mid)
        sheet.write(row+2,6, '', head_cell_format_down)

        sheet.write(row,7, 'สินค้า', head_cell_format_up)
        sheet.write(row+1,7, commission_types[0].name or 'COM001', head_cell_format_mid)
        sheet.write(row+2,7, 'ก่อนภาษี', head_cell_format_down)

        sheet.write(row,8, 'สินค้า', head_cell_format_up)
        sheet.write(row+1,8, commission_types[1].name or  'COM002', head_cell_format_mid)
        sheet.write(row+2,8, 'ก่อนภาษี', head_cell_format_down)

        sheet.write(row,9, 'สินค้า', head_cell_format_up)
        sheet.write(row+1,9, commission_types[2].name or  'COM003', head_cell_format_mid)
        sheet.write(row+2,9, 'ก่อนภาษี', head_cell_format_down)

        sheet.write(row,10, 'สินค้าปกติ', head_cell_format_up)
        sheet.write(row+1,10, '', head_cell_format_mid)
        sheet.write(row+2,10, 'ก่อนภาษี', head_cell_format_down)

        sheet.write(row,11, 'ยอดก่อนภาษี', head_cell_format_up)
        sheet.write(row+1,11, '', head_cell_format_mid)
        sheet.write(row+2,11, '', head_cell_format_down)

        sheet.write(row,12, 'หมายเหตุ', head_cell_format_up)
        sheet.write(row+1,12, '', head_cell_format_mid)
        sheet.write(row+2,12, '', head_cell_format_down)

        

        column_widths = {
            0: 8,  # A
            1: 8,  # B
            2: 9,  # C
            3: 10,  # D
            4: 10,  # E
            5: 15,  # F
            6: 22,  # G
            7: 8,  # H
            8: 8,  # I
            9: 8,  # J
            10: 8,  # K
            11: 8,  # L
            12: 10,  # M
            13: 10,  # N
            14: 10,  # O
            15: 10,  # P
            16: 10, # Q
            17: 10, # R
            18: 10, # S
            19: 10, # T
        }

        for col, width in column_widths.items():
            sheet.set_column(col, col, width)

        
        row = 4
        number = 0
        total_amount_untax = 0
        total_amount_untax_sum_all = 0
        total_amount_commission_1_untax = 0
        total_amount_commission_1_untax_sum_all = 0
        total_amount_commission_2_untax = 0
        total_amount_commission_2_untax_sum_all = 0
        total_amount_commission_3_untax = 0
        total_amount_commission_3_untax_sum_all = 0
        total_amount_no_com = 0
        total_amount_no_com_sum_all = 0
        for item in payment_lines:
            
            row += 1
            number += 1
            total_amount_untax = item.total_amount_untax
            total_amount_untax_sum_all = total_amount_untax_sum_all + total_amount_untax
            total_amount_commission_1_untax = 0
            total_amount_commission_2_untax = 0
            total_amount_commission_3_untax = 0
            total_amount_no_com = 0
            
            if commission_types[0].id in item.product_id.commission_type.ids:
                total_amount_commission_1_untax = total_amount_untax
                total_amount_commission_1_untax_sum_all = total_amount_commission_1_untax_sum_all + total_amount_untax
            elif commission_types[1].id in item.product_id.commission_type.ids:
                total_amount_commission_2_untax = total_amount_untax
                total_amount_commission_2_untax_sum_all = total_amount_commission_2_untax_sum_all + total_amount_untax
            elif commission_types[2].id in item.product_id.commission_type.ids:
                total_amount_commission_3_untax = total_amount_untax
                total_amount_commission_3_untax_sum_all = total_amount_commission_3_untax_sum_all + total_amount_untax
            else:
                total_amount_no_com = total_amount_untax
                total_amount_no_com_sum_all = total_amount_no_com_sum_all + total_amount_untax

            data_list_1 = [
                        str(settle_commissions_id.commission_date.strftime('%d/%m/%y')), 
                        str(item.payment_id_date.strftime('%d/%m/%y')) or '',
                        str(item.invoice_id_date.strftime('%d/%m/%y')) or '',
                        item.form_no or '',
                        item.payment_id.name or '',]
            data_list_1_2 = [
                        item.partner_id.name or '',
                        item.product_id.name or '',
                        '',
                        '',
                        '',
                        '',
                        '',
                        item.note or '',
                        ]
            if item.product_id.type == 'service':
                total_amount_untax = 0
                
            sheet.write_row(row,0, data_list_1,data_cell_format)
            sheet.write_row(row,5, data_list_1_2,data_cell_format_left)
            data_list_2 = [ total_amount_commission_1_untax or '',
                            total_amount_commission_2_untax or '',
                            total_amount_commission_3_untax or '',
                            total_amount_no_com or '',
                            total_amount_untax or '',]
            sheet.write_row(row,7, data_list_2,data_cell_number_format)
                    
        row += 1
        
        data_list_2 = [ total_amount_commission_1_untax_sum_all or '',
                        total_amount_commission_2_untax_sum_all or '',
                        total_amount_commission_3_untax_sum_all or '',
                        total_amount_no_com_sum_all or '',
                        total_amount_untax_sum_all or '',]
        sheet.write_row(row,7, data_list_2,data_cell_number_format_sum)
    
                    