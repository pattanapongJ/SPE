# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
import pytz
import datetime
from datetime import datetime, date, time
from decimal import Decimal, ROUND_HALF_UP
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError, except_orm

class PartnerXlsx(models.AbstractModel):
    _name = 'report.stock_movement_report_xlsx'
    _description = 'report.stock_movement_report_xlsx'
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
            'border': True
        })
        top_cell_format.set_font_size(16)
        top_cell_format.set_align('vcenter')
        top_cell_format.set_font_name('Kanit')
        date_cell_format = workbook.add_format({
            'align': 'center',
            'border': True,
        })
        date_cell_format.set_font_size(12)
        date_cell_format.set_align('vcenter')
        date_cell_format.set_font_name('Kanit')
        head_cell_format = workbook.add_format({
            'align': 'center',
            'border': True,
            'bg_color': '#A8A9E3'
        })
        head_cell_format.set_font_size(12)
        head_cell_format.set_align('vcenter')
        head_cell_format.set_font_name('Kanit')
        data_cell_format = workbook.add_format({
            'border': True,
            'align': 'top'
        })
        data_cell_format.set_font_size(9)
        data_cell_format.set_align('vcenter')
        data_cell_format.set_font_name('Kanit')
        data_cell_number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': True,
            'align': 'top'
        })
        data_cell_number_format.set_font_size(9)
        data_cell_number_format.set_align('vcenter')
        data_cell_number_format.set_font_name('Kanit')
        format_footerC_bold2_2_2 = workbook.add_format({'align': 'center', 'bottom': True, 'left': True, 'right': True})
        format_footerC_bold2_2_2.set_font_name('Kanit')
        format_footerC_bold2_2_3 = workbook.add_format({'align': 'center', 'left': True, 'right': True})
        format_footerC_bold2_2_3.set_font_size(11)
        format_footerC_bold2_2_3.set_font_size(11)
        format_footerC_bold2_2_3.set_font_name('Kanit')

        # report name
        report_name = ("รายงานการเคลื่อนไหวของสินค้า")
        sheet = workbook.add_worksheet(report_name)
        sheet.merge_range('A1:R1', partners.company_id.name_th, top_cell_format)
        sheet.merge_range('A2:R2', 'รายงานการเคลื่อนไหวของสินค้า (Stock Movement Report)', top_cell_format)
        sheet.set_row(0, 20)
        sheet.set_row(1, 15)
        sheet.set_row(2, 15)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 3, 20)
        sheet.set_column(4, 4, 40)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 8, 15)
        sheet.set_column(9, 12, 15)

        # #Header
        data_user_text1 = '          ลงชื่อ _________________________          ลงชื่อ _________________________            ลงชื่อ _________________________'
        data_user_text = '    ผู้จัดทำ ' + str(
            res_users.name) + '                                           ผู้ตรวจสอบ                                                      ผู้อนุมัติ'

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
                    text_month_from = 'มกราคม'
                if int(month_from) == 2:
                    text_month_from = 'กุมภาพันธ์'
                if int(month_from) == 3:
                    text_month_from = 'มีนาคม'
                if int(month_from) == 4:
                    text_month_from = 'เมษายน'
                if int(month_from) == 5:
                    text_month_from = 'พฤษภาคม'
                if int(month_from) == 6:
                    text_month_from = 'มิถุนายน'
                if int(month_from) == 7:
                    text_month_from = 'กรกฎาคม'
                if int(month_from) == 8:
                    text_month_from = 'สิงหาคม'
                if int(month_from) == 9:
                    text_month_from = 'กันยายน'
                if int(month_from) == 10:
                    text_month_from = 'ตุลาคม'
                if int(month_from) == 11:
                    text_month_from = 'พฤศจิกายน'
                if int(month_from) == 12:
                    text_month_from = 'ธันวาคม'
            if year_from:
                year_from = int(year_from) + 543

        if date_to:
            day_to = str(date_to).split('-')[2]
            month_to = str(date_to).split('-')[1]
            year_to = str(date_to).split('-')[0]
            if month_to:
                if int(month_to) == 1:
                    text_month_to = 'มกราคม'
                if int(month_to) == 2:
                    text_month_to = 'กุมภาพันธ์'
                if int(month_to) == 3:
                    text_month_to = 'มีนาคม'
                if int(month_to) == 4:
                    text_month_to = 'เมษายน'
                if int(month_to) == 5:
                    text_month_to = 'พฤษภาคม'
                if int(month_to) == 6:
                    text_month_to = 'มิถุนายน'
                if int(month_to) == 7:
                    text_month_to = 'กรกฎาคม'
                if int(month_to) == 8:
                    text_month_to = 'สิงหาคม'
                if int(month_to) == 9:
                    text_month_to = 'กันยายน'
                if int(month_to) == 10:
                    text_month_to = 'ตุลาคม'
                if int(month_to) == 11:
                    text_month_to = 'พฤศจิกายน'
                if int(month_to) == 12:
                    text_month_to = 'ธันวาคม'
            if year_to:
                year_to = int(year_to) + 543

        date_show = 'จากวันที่ ' + str(day_from) + ' ' + str(text_month_from) + ' ' + str(year_from) + ' ถึง ' + str(
            day_to) + ' ' + str(text_month_to) + ' ' + str(year_to)

        sheet.merge_range('A3:R3', date_show, date_cell_format)
        sheet.merge_range('A4:A5', 'ลำดับที่\n', head_cell_format)
        sheet.merge_range('B4:B5', 'WH\n', head_cell_format)
        sheet.merge_range('C4:C5', 'Product Type', head_cell_format)
        sheet.merge_range('D4:D5', 'Product Category\n', head_cell_format)

        sheet.merge_range('E4:E5', 'เลขที่เอกสาร', head_cell_format)
        sheet.merge_range('F4:F5', 'เลขที่ออเดอร์\n', head_cell_format)
        sheet.merge_range('G4:G5', 'วันนำเข้า\nออก', head_cell_format)
        sheet.merge_range('H4:H5', 'รหัสสินค้า\n', head_cell_format)
        sheet.merge_range('I4:I5', 'ชื่อสินค้า\n', head_cell_format)
        sheet.merge_range('J4:J5', 'Cost\n(THB/Unit)\n', head_cell_format)

        sheet.merge_range('K5:L5', 'ปริมาณ', head_cell_format)
        sheet.merge_range('K4:L4', 'ยอดยกมา', head_cell_format)
        sheet.merge_range('M5:N5', 'ปริมาณ', head_cell_format)
        sheet.merge_range('M4:N4', 'นำเข้า', head_cell_format)
        sheet.merge_range('O5:P5', 'ปริมาณ', head_cell_format)
        sheet.merge_range('O4:P4', 'เบิกออก', head_cell_format)

        sheet.merge_range('Q4:Q5', 'คงเหลือ\n', head_cell_format)
        sheet.merge_range('R4:R5', 'หน่วยนับ\n', head_cell_format)

        column_widths = {
            0: 15,  # A
            1: 20,  # B
            2: 30,  # C
            3: 30,  # D
            4: 20,  # B
            5: 30,  # C
            6: 30,  # D
            7: 30,  # E
            8: 30,  # D
            9: 30,  # F
            10: 15,  # G
            11: 15,  # H
            12: 15,  # I
            13: 15, # J
            14: 15, # K
            15: 15, # L
            16: 15, # M
        }

        for col, width in column_widths.items():
            sheet.set_column(col, col, width)

        search = []

        row = 4
        number = 0
        in_total = 0
        out_total = 0
        qty_total = 0
        before_total_sum = 0

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

                    stock_move_id = self.env['stock.move'].search(
                    [('date', '<=', date_to), ('date', '>=', date_from), ('state', '=', 'done'), ('warehouse_id', '=', warehouse_id.id),
                     ('product_id', '=', product_ids.id)], order="date")

                else:
                    stock_quant = self.env['stock.quant'].search(
                    [('create_date', '<', date_from), ('product_id', '=', product_ids.id),('location_id.usage', 'in', ('internal', 'transit'))])

                    stock_move_id = self.env['stock.move'].search(
                        [('date', '<=', date_to), ('date', '>=', date_from), ('state', '=', 'done'),
                        ('product_id', '=', product_ids.id)], order="date")

            else:
                stock_movebefore_id = False
                
                if warehouse_id:
                    stock_move_id = self.env['stock.move'].search(
                        [('state', '=', 'done'), ('product_id', '=', product_ids.id), ('warehouse_id', '=', warehouse_id.id), ('location_id.usage', 'not in', ('internal', 'transit')), ('location_dest_id.usage', 'in', ('internal', 'transit'))], order="date")
                
                else:
                    stock_move_id = self.env['stock.move'].search(
                        [('state', '=', 'done'), ('product_id', '=', product_ids.id), ('location_id.usage', 'not in', ('internal', 'transit')), ('location_dest_id.usage', 'in', ('internal', 'transit'))], order="date")
            
            if stock_move_id:
                row += 1

                if stock_quant:
                    for before_stock_quant_ids in stock_quant:
                        amount_before += before_stock_quant_ids.quantity
                before_total = before_total + amount_before
                amount_qty = before_total
                qty_total += amount_qty

                data_list = ["",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                product_ids.name or "",
                                before_total or 0,
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                "",
                                ]
                
                merge_row = 'K' + str(row + 1) + ':L' + str(row + 1)
                sheet.merge_range(merge_row, '', data_cell_format)

                merge_row1 = 'M' + str(row + 1) + ':N' + str(row + 1)
                sheet.merge_range(merge_row1, '', data_cell_format)

                merge_row2 = 'O' + str(row + 1) + ':P' + str(row + 1)
                sheet.merge_range(merge_row2, '', data_cell_format)

                sheet.write_row(row,0, data_list, data_cell_format)                
                
                for stock_move_ids in stock_move_id:
                    mo_id = self.env['mrp.production'].search([('name', '=', stock_move_ids.origin)],limit=1)
                    if stock_move_ids.location_id.usage not in ('internal', 'transit') and stock_move_ids.location_dest_id.usage in ('internal', 'transit'):
                        row += 1
                        number += 1

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            amount_qty = amount_qty + stock_move_ids.product_uom_qty
                            in_amount = in_amount + stock_move_ids.product_uom_qty
                            qty_9 = stock_move_ids.product_uom_qty

                        elif stock_move_ids.location_id.usage == 'internal':
                            amount_qty = amount_qty - stock_move_ids.product_uom_qty
                            out_amount = out_amount + stock_move_ids.product_uom_qty

                            qty_11 = stock_move_ids.product_uom_qty

                        qty_total += amount_qty

                        if product_ids.type:
                            pd_type = product_ids.type
                            pd_type_name = self.get_selection(pd_type)

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            data_list_1 = [
                                    number, 
                                    stock_move_ids.warehouse_id.name or "",
                                    pd_type_name,
                                    product_ids.categ_id.complete_name,
                                    stock_move_ids.origin or '', 
                                    stock_move_ids.reference, 
                                    str(stock_move_ids.date), 
                                    product_ids.default_code or '', 
                                    product_ids.name]
                            data_list_1_2 = [
                                    product_ids.standard_price,
                                    "", 
                                    "", 
                                    qty_9 or '', 
                                    "", 
                                    "",
                                    "", 
                                    amount_qty or '']
                        elif stock_move_ids.location_id.usage == 'internal':
                            data_list_1 = [
                                    number, 
                                    stock_move_ids.warehouse_id.name or "",
                                    pd_type_name,
                                    product_ids.categ_id.complete_name,
                                    stock_move_ids.origin or '', 
                                    stock_move_ids.reference, 
                                    str(stock_move_ids.date), 
                                    product_ids.default_code or '', 
                                    product_ids.name]
                            data_list_1_2 = [
                                    product_ids.standard_price,
                                    "", 
                                    "", 
                                    "",
                                    "", 
                                    qty_11 or '', 
                                    "", 
                                    amount_qty or ''
                                    ]

                        merge_row = 'K' + str(row + 1) + ':L' + str(row + 1)
                        sheet.merge_range(merge_row, '', data_cell_format)

                        merge_row1 = 'M' + str(row + 1) + ':N' + str(row + 1)
                        sheet.merge_range(merge_row1, '', data_cell_format)

                        merge_row2 = 'O' + str(row + 1) + ':P' + str(row + 1)
                        sheet.merge_range(merge_row2, '', data_cell_format)

                        sheet.write_row(row,0, data_list_1, data_cell_format)
                        sheet.write_row(row,9, data_list_1_2, data_cell_number_format)
                        sheet.write(row,17, product_ids.uom_id.name or '', data_cell_format)

                    elif stock_move_ids.location_id.usage in ('internal', 'transit') and stock_move_ids.location_dest_id.usage not in ('internal', 'transit'):
                        row += 1
                        number += 1

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            amount_qty = amount_qty + stock_move_ids.product_uom_qty
                            in_amount = in_amount + stock_move_ids.product_uom_qty

                            qty_9 = stock_move_ids.product_uom_qty

                        elif stock_move_ids.location_id.usage == 'internal':
                            amount_qty = amount_qty - stock_move_ids.product_uom_qty
                            out_amount = out_amount + stock_move_ids.product_uom_qty

                            qty_11 = stock_move_ids.product_uom_qty

                        qty_total += amount_qty

                        if product_ids.type:
                            pd_type = product_ids.type
                            pd_type_name = self.get_selection(pd_type)

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            data_list_2 = [number,
                                            stock_move_ids.warehouse_id.name or "",
                                            pd_type_name,
                                            product_ids.categ_id.complete_name,
                                            stock_move_ids.origin or '',
                                            stock_move_ids.reference,
                                            str(stock_move_ids.date),
                                            product_ids.default_code or '',
                                            product_ids.name]
                            data_list_2_2 = [
                                            product_ids.standard_price,
                                            "",
                                            "",
                                            qty_9 or '',
                                            "",
                                            "",
                                            '',
                                            amount_qty or '',
                                        ]
                        elif stock_move_ids.location_id.usage == 'internal':
                            data_list_2 = [number,
                                            stock_move_ids.warehouse_id.name or "",
                                            pd_type_name,
                                            product_ids.categ_id.complete_name,
                                            stock_move_ids.origin or '',
                                            stock_move_ids.reference,
                                            str(stock_move_ids.date),
                                            product_ids.default_code or '',
                                            product_ids.name]
                            data_list_2_2 = [
                                            product_ids.standard_price,
                                            "",
                                            "",
                                            "",
                                            "",
                                            qty_11 or '',
                                            '',
                                            amount_qty or '',
                                        ]
                        
                        merge_row = 'K' + str(row + 1) + ':L' + str(row + 1)
                        sheet.merge_range(merge_row, '', data_cell_format)

                        merge_row1 = 'M' + str(row + 1) + ':N' + str(row + 1)
                        sheet.merge_range(merge_row1, '', data_cell_format)

                        merge_row2 = 'O' + str(row + 1) + ':P' + str(row + 1)
                        sheet.merge_range(merge_row2, '', data_cell_format)

                        sheet.write_row(row,0, data_list_2, data_cell_format)
                        sheet.write_row(row,9, data_list_2_2, data_cell_number_format)
                        sheet.write(row,17, product_ids.uom_id.name or '', data_cell_format)

                in_total = in_total + in_amount
                out_total = out_total + out_amount
            before_total_sum += before_total
        row += 1
        sheet.merge_range(row, 0, row, 9, 'รวมทั้งสิ้น', data_cell_format)
        sheet.merge_range(row, 10, row, 11, before_total_sum, data_cell_number_format)
        sheet.merge_range(row, 12, row, 13, in_total, data_cell_number_format)
        sheet.merge_range(row, 14, row, 15, out_total, data_cell_number_format)

        sheet.write(row, 16, '', data_cell_format)
        sheet.write(row, 17, '', data_cell_format)

        merge_row = 'A' + str(row + 2) + ':' + 'R' + str(row + 2)
        sheet.merge_range(merge_row, '', format_footerC_bold2_2_3)
        merge_row1 = 'A' + str(row + 3) + ':' + 'R' + str(row + 3)
        sheet.merge_range(merge_row1, data_user_text1, format_footerC_bold2_2_3)
        merge_row2 = 'A' + str(row + 4) + ':' + 'R' + str(row + 4)
        sheet.merge_range(merge_row2, data_user_text, format_footerC_bold2_2_3)
        merge_row3 = 'A' + str(row + 5) + ':' + 'R' + str(row + 5)
        sheet.merge_range(merge_row3, '', format_footerC_bold2_2_2)
        