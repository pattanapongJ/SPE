# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
import pytz
import datetime
from datetime import datetime, date, time, timedelta

from decimal import Decimal, ROUND_HALF_UP
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError, except_orm

class PartnerXlsx(models.AbstractModel):
    _name = 'report.quotation_project_bo_xlsx'
    _description = 'report.quotation_project_bo_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        
        project_name = objects.project_name
        start_date = objects.date_from
        to_date = objects.date_to
        date_from = objects.date_from
        date_to = objects.date_to
        start_date = start_date.strftime("%Y-%m-%d 00:00:00")
        to_date = to_date.strftime("%Y-%m-%d 23:59:59")

        domain = [('state', '=', 'draft'), ('date_order', '<=', date_to), ('date_order', '>=', date_from)]
        if project_name:
            project_name_ids = project_name.ids  # ดึง ID ของแผนก
            domain.append(('project_name', 'in', project_name_ids))  # ใช้ 'in' แทน '='
        
        qo_id = self.env['quotation.order'].search(domain)
        # format
        data_bold_cell_format = workbook.add_format({
            'bold': True,
            'align': 'left',
        })

        head_sub_cell_format_top_border = workbook.add_format({
            'align': 'center',
            # 'bold': True,
            'top': 1, 
        })

        head_sub_cell_format_top_border.set_font_size(9)
        head_sub_cell_format_top_border.set_align('vcenter')
        head_sub_cell_format_top_border.set_font_name('Kanit')

        head_sub_cell_format_no_border = workbook.add_format({
            'align': 'center',
            # 'bold': True,
            # 'top': 1, 
        })

        head_sub_cell_format_no_border.set_font_size(9)
        head_sub_cell_format_no_border.set_align('vcenter')
        head_sub_cell_format_no_border.set_font_name('Kanit')

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

        data_cell_format_left_cus = workbook.add_format({
            'align': 'left',
            'border': False,
        })
        data_cell_format_left_cus.set_font_size(9)
        data_cell_format_left_cus.set_align('vcenter')
        data_cell_format_left_cus.set_font_name('Kanit')

        border_format_buttom = workbook.add_format({
            'bottom': 1,  # เส้นขอบล่างบาง
        })

        head_sub_cell_format_cus = workbook.add_format({
            'align': 'center',
            'bold': True,
            'bottom': 1,
        })
        head_sub_cell_format_cus.set_font_size(9)
        head_sub_cell_format_cus.set_align('vcenter')
        head_sub_cell_format_cus.set_font_name('Kanit')
        head_sub_cell_format_cus.set_bottom(1)

        top_cell_format = workbook.add_format({
            'bold': True,
            'align': 'left',
            'border': True
        })
        top_cell_format.set_font_size(16)
        top_cell_format.set_align('vcenter')
        date_cell_format = workbook.add_format({
            'align': 'left',
            'border': True,
        })
        date_cell_format.set_font_size(12)
        date_cell_format.set_align('vcenter')
        head_cell_format = workbook.add_format({
            'align': 'center',
            'border': True,
            'bg_color': '#A8A9E3'
        })
        head_cell_format.set_font_size(12)
        head_cell_format.set_align('vcenter')
        data_cell_format = workbook.add_format({
            'border': True,
            'align': 'top'
        })

        head_sub_cell_format_cus = workbook.add_format({
            'align': 'center',
            'bold': True,
            'bottom': 1,
        })
        head_sub_cell_format_cus.set_font_size(9)
        head_sub_cell_format_cus.set_align('vcenter')
        head_sub_cell_format_cus.set_font_name('Kanit')
        head_sub_cell_format_cus.set_bottom(1)

        format_footerC_bold2_2_2 = workbook.add_format({'align': 'center', 'bottom': True, 'left': True, 'right': True})
        format_footerC_bold2_2_3 = workbook.add_format({'align': 'center', 'left': True, 'right': True})
        format_footerC_bold2_2_3.set_font_size(11)
        format_footerC_bold2_2_3.set_font_size(11)

        data_cell_format_left = workbook.add_format({
            'align': 'left',
            'border': False,
        })
        data_cell_format_left.set_font_size(9)
        data_cell_format_left.set_align('vcenter')

        # report name
        report_name = ("Quotation Project Bo")
        sheet = workbook.add_worksheet(report_name)
        sheet.merge_range('A1:T1', 'SPE Quotation Project (Bo)', top_cell_format)
        sheet.merge_range('A2:T2', 'Saeng Charoen Group', top_cell_format)
        sheet.set_row(0, 20)
        sheet.set_row(1, 15)
        sheet.set_row(2, 15)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 3, 20)
        sheet.set_column(4, 4, 40)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 8, 15)
        sheet.set_column(9, 12, 15)

        row = 3
        for item in qo_id:
            row +=1
            sheet.write(row,0, 'Quotation', head_sub_cell_format)
            sheet.write(row,1, 'Customer', head_sub_cell_format)
            sheet.write(row,2, '', head_sub_cell_format)
            sheet.merge_range(row,3,row,4, 'QuotDate', head_sub_cell_format)
            sheet.merge_range(row,5,row,6, 'Amount', head_sub_cell_format)
            sheet.merge_range(row,7,row,8, 'Sales Respond', head_sub_cell_format)
            sheet.merge_range(row,9,row,11, 'Customer Req', head_sub_cell_format)
            sheet.merge_range(row,12,row,13, 'Project Description', head_sub_cell_format)
            sheet.write(row,14, '', head_sub_cell_format)
            sheet.write(row,15, '', head_sub_cell_format)
            sheet.write(row,16, '', head_sub_cell_format)
            sheet.write(row,17, '', head_sub_cell_format)

            row +=1
            sheet.write(row,0, '', head_sub_cell_format)
            sheet.write(row,1, '', head_sub_cell_format)
            sheet.write(row,2, '', head_sub_cell_format)
            sheet.merge_range(row,3,row,4, 'ExpDate', head_sub_cell_format)
            sheet.merge_range(row,5,row,6, '', head_sub_cell_format)
            sheet.merge_range(row,7,row,8, 'Sales Spec', head_sub_cell_format)
            sheet.merge_range(row,9,row,11, 'Remark', head_sub_cell_format)
            sheet.merge_range(row,12,row,17, '', head_sub_cell_format)
            row +=1
            sheet.write(row,0, 'ItemId', head_sub_cell_format)
            sheet.write(row,1, '', head_sub_cell_format)
            sheet.write(row,2, 'Vat', head_sub_cell_format)
            sheet.write(row,3, 'จำนวน', head_sub_cell_format)
            sheet.write(row,4, 'หน่วย', head_sub_cell_format)
            sheet.merge_range(row,5,row,6, 'ราคาเสนอลูกค้า', head_sub_cell_format)
            sheet.write(row,7, 'Disc.per 1', head_sub_cell_format)
            sheet.write(row,8, 'Disc.per 2', head_sub_cell_format)
            sheet.write(row,9, 'จำนวนเงิน', head_sub_cell_format)
            sheet.write(row,10, 'ราคาตั้ง', head_sub_cell_format)
            sheet.write(row,11, 'transfer 24', head_sub_cell_format_warp)
            sheet.write(row,12, 'Transfer อื่น', head_sub_cell_format)
            sheet.write(row,13, 'ค้างรับ', head_sub_cell_format)
            sheet.write(row,14, 'ค้างส่ง', head_sub_cell_format)
            sheet.write(row,15, 'Physical Inv', head_sub_cell_format_warp)
            sheet.write(row,16, '02-SP-PRO', head_sub_cell_format)
            sheet.write(row,17, '02-SPวันที่เริ่มต้น/สิ้นสุด', head_sub_cell_format)

            column_widths = {
                0: 15,  # A
                1: 35,  # B
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
                12: 15,  # F
                13: 15,  # F
                14: 15,  # F
                15: 15,  # F
                16: 15,  # F
                17: 15,  # F

            }

            for col, width in column_widths.items():
                sheet.set_column(col, col, width)

            row += 1

            if item.quotation_line:
                tax_names = ', '.join(map(lambda x: x.name, item.quotation_line.tax_id))

            sheet.write_row(row, 0, item.name or '', head_sub_cell_format_top_border)
            sheet.write_row(row, 1, item.partner_id.name or '', head_sub_cell_format_top_border)
            sheet.write_row(row, 2, tax_names or '', head_sub_cell_format_top_border)
            sheet.merge_range(row, 3, row, 4, item.date_order.strftime('%Y-%m-%d') if item.date_order else '', head_sub_cell_format_top_border)
            sheet.merge_range(row, 5, row, 6, item.amount_total or 0, head_sub_cell_format_top_border)
            sheet.merge_range(row, 7, row, 8, item.user_id.name or '', head_sub_cell_format_top_border)
            sheet.merge_range(row, 9, row, 11, item.partner_id.name or '', head_sub_cell_format_top_border)
            sheet.merge_range(row, 12, row, 17, item.project_name.project_name or '', head_sub_cell_format_top_border)
            row += 1
            sheet.write_row(row, 0, '', head_sub_cell_format_no_border)
            sheet.write_row(row, 1, '', head_sub_cell_format_no_border)
            sheet.write_row(row, 2, '', head_sub_cell_format_no_border)
            sheet.merge_range(row, 3, row, 4, item.validity_date.strftime('%Y-%m-%d') if item.validity_date else '', head_sub_cell_format_no_border)
            sheet.merge_range(row, 5, row, 6, '', head_sub_cell_format_no_border)
            sheet.merge_range(row, 7, row, 8, item.sale_spec.name or '', head_sub_cell_format_no_border)
            sheet.merge_range(row, 9, row, 11, item.remark or '', head_sub_cell_format_no_border)
            sheet.merge_range(row, 12, row, 17, '', head_sub_cell_format_no_border)
            # row += 1
            # sheet.merge_range(row,0,row,17, '',border_format_buttom)

            row += 3

            transfer24_dict = {}
            transfer_other_dict = {}
            batch_dict = {} #ค้างรับ
            picking_list_dict = {} #ค้างส่ง
            physical_inv_dict = {}

            for i, line in enumerate(item.quotation_line):
                if line:
                    line_tax_names = ', '.join(map(lambda x: x.name, line.tax_id))
                
                product_id = line.product_id.id
                transfer24_total = 0
                transfer_other_total = 0
                batch_total = 0
                picking_list_total = 0
                physical_inv_total = 0
                in_amount = 0
                out_amount = 0

                picking_ids_24 = self.env['stock.picking'].search([
                    ('addition_operation_types.code', '=', "AO-06"),
                    ('order_id', '!=', False),
                    ('state', '=', 'done'),
                    ('from_warehouse.code', 'in', ['C-24A', 'C-24B'])
                ])

                picking_ids_other = self.env['stock.picking'].search([
                    ('addition_operation_types.code', '=', "AO-06"),
                    ('order_id', '!=', False),
                    ('state', '=', 'done'),
                    ('from_warehouse.code', 'not in', ['C-24A', 'C-24B'])
                ])

                # batch_ids = self.env['stock.picking.batch'].search([
                #     ('state', 'in', ['draft', 'in_progress'])
                # ])

                picking_list_ids = self.env['picking.lists'].search([
                    ('state', 'in', ['draft', 'waiting_pick'])
                ])

                for picking_24 in picking_ids_24:
                    transfer24_total += sum(picking_24.move_ids_without_package.filtered(
                        lambda move: move.product_id.id == product_id
                    ).mapped('product_uom_qty'))
                
                for picking_other in picking_ids_other:
                    transfer_other_total += sum(picking_other.move_ids_without_package.filtered(
                        lambda move: move.product_id.id == product_id
                    ).mapped('product_uom_qty'))

                # for batch in batch_ids:
                #     batch_total += sum(batch.move_line_tranfer_ids.filtered(
                #         lambda move: move.product_id.id == product_id
                #     ).mapped('product_uom_qty'))

                for picking_list in picking_list_ids:
                    picking_list_total += sum(picking_list.list_line_ids.filtered(
                        lambda move: move.product_id.id == product_id
                    ).mapped('qty'))

                stock_move_id = self.env['stock.move.line'].search([
                    ('state', '=', 'done'),
                    ('product_id', '=', product_id)
                ])

                if stock_move_id:
                    for stock_move_ids in stock_move_id:
                        qty = stock_move_ids.product_uom_id._compute_quantity(stock_move_ids.qty_done, stock_move_ids.product_id.uom_id)

                        # คำนวณการส่งสินค้า
                        if stock_move_ids.location_id.usage in ('internal', 'transit'):
                            out_amount += qty

                        # คำนวณการรับสินค้า
                        if stock_move_ids.location_dest_id.usage in ('internal', 'transit'):
                            in_amount += qty

                # คำนวณค่ารวมสำหรับผลิตภัณฑ์นี้
                total_amount = in_amount - out_amount  # สามารถปรับสูตรตามที่ต้องการได้

                # บันทึก in_amount, out_amount และผลรวมใน physical_inv_dict
                physical_inv_dict[product_id] = {
                    'in_amount': in_amount,
                    'out_amount': out_amount,
                    'total_amount': total_amount  # ยอดรวมที่คำนวณ
                }

                transfer24_dict[product_id] = transfer24_total
                transfer_other_dict[product_id] = transfer_other_total
                batch_dict[product_id] = batch_total
                picking_list_dict[product_id] = picking_list_total

                sheet.write_row(row,0, [line.product_id.default_code] or '',data_cell_format_left)
                sheet.write_row(row,1, [line.product_id.name] or '',data_cell_format_left)
                sheet.write_row(row,2, [line_tax_names] or '',data_cell_format_left)
                sheet.write_row(row, 3, [line.product_uom_qty] or '', data_cell_format_left)
                sheet.write_row(row,4, [line.product_uom.name] or '',data_cell_format_left) 
                sheet.merge_range(row,5,row,6, line.price_unit or '',data_cell_format_left) 
                sheet.write_row(row,7, ['Disc per 1'],data_cell_format_left) 
                sheet.write_row(row,8, ['Disc per 2'],data_cell_format_left) 
                sheet.write_row(row, 9, [line.product_uom_qty * line.price_unit] or '', data_cell_format_left)
                sheet.write_row(row,10, [item.pricelist_id.item_ids.filtered(lambda items: items.product_id.id == line.product_id.id).sorted(key=lambda items: items.write_date, reverse=True)[0].price if item.pricelist_id and item.pricelist_id.item_ids.filtered(lambda items: items.product_id.id == line.product_id.id) else ''],data_cell_format_left) 
                sheet.write_row(row,11, [transfer24_dict.get(line.product_id.id, 0)],data_cell_format_left)
                sheet.write_row(row,12, [transfer_other_dict.get(line.product_id.id, 0)],data_cell_format_left)
                sheet.write_row(row,13, [batch_dict.get(line.product_id.id, 0)],data_cell_format_left)
                sheet.write_row(row,14, [picking_list_dict.get(line.product_id.id, 0)],data_cell_format_left)
                sheet.write_row(row,15, [physical_inv_dict.get(line.product_id.id, {}).get('total_amount', 0)],data_cell_format_left)
                sheet.write_row(row,16, ['02-SP-PRO'],data_cell_format_left)
                sheet.write_row(row,17, ['02-เริ่มสิ้น'],data_cell_format_left)

                row += 1

        
            row += 2
        
