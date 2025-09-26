# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
import pytz
import datetime
from datetime import datetime, date, time, timedelta

from decimal import Decimal, ROUND_HALF_UP
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError, except_orm

class SaleInterCompanyXlsx(models.AbstractModel):
    _name = 'report.sale_inter_company_xlsx'
    _description = 'report.sale_inter_company_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        
        date_from = objects.from_date
        date_to = objects.to_date
        product_ids = objects.product_ids
        tax_filter = objects.tax

        # Base domain for IC transactions
        domain_ic = [('date_order', '<=', date_to), ('date_order', '>=', date_from),('type_id.inter_company_transactions','=',True)]
        
        # Base domain for SO transactions
        domain_so = [('date_order', '<=', date_to), ('date_order', '>=', date_from),('type_id.inter_company_transactions','=',False),('inter_so_company','!=',False)]
        
        # Add product filter if specified
        if product_ids:
            domain_ic.append(('order_line.product_id', 'in', product_ids.ids))
            domain_so.append(('order_line.product_id', 'in', product_ids.ids))
        
        so_id_ic = self.env['sale.order'].search(domain_ic)
        so_id_so = self.env['sale.order'].search(domain_so)

        # Define all formats
        formats = self._get_worksheet_formats(workbook)

        # If products are filtered, create separate tabs for each product
        if product_ids:
            for product in product_ids:
                sheet_name = f"{product.default_code or product.name}"[:31]  # Excel sheet name limit
                sheet = workbook.add_worksheet(sheet_name)
                self._setup_worksheet_headers(sheet, formats)
                
                # Filter data for this specific product
                product_so_ic = so_id_ic.filtered(lambda so: any(line.product_id.id == product.id for line in so.order_line))
                product_so_so = so_id_so.filtered(lambda so: any(line.product_id.id == product.id for line in so.order_line))
                
                row = self._write_data_to_sheet(sheet, formats, product_so_ic, product_so_so, product.id, tax_filter)
        else:
            # Create single sheet for all products
            report_name = ("รายงานซื้อขายระหว่างกัน")
            sheet = workbook.add_worksheet(report_name)
            self._setup_worksheet_headers(sheet, formats)
            row = self._write_data_to_sheet(sheet, formats, so_id_ic, so_id_so, None, tax_filter)

    def _get_worksheet_formats(self, workbook):
        """Define all worksheet formats"""
        formats = {}
        
        formats['data_bold_cell_format'] = workbook.add_format({
            'bold': True,
            'align': 'left',
        })

        formats['head_sub_cell_format'] = workbook.add_format({
            'align': 'center',
            'bold': True,
            'top': 1, 
        })

        formats['head_sub_cell_format_top_border'] = workbook.add_format({
            'align': 'center',
            'top': 1, 
        })
        formats['head_sub_cell_format_top_border'].set_font_size(9)
        formats['head_sub_cell_format_top_border'].set_align('vcenter')
        formats['head_sub_cell_format_top_border'].set_font_name('Kanit')

        formats['head_sub_cell_format_no_border'] = workbook.add_format({
            'align': 'center',
        })
        formats['head_sub_cell_format_no_border'].set_font_size(9)
        formats['head_sub_cell_format_no_border'].set_align('vcenter')
        formats['head_sub_cell_format_no_border'].set_font_name('Kanit')

        formats['head_sub_cell_format'].set_font_size(9)
        formats['head_sub_cell_format'].set_align('vcenter')
        formats['head_sub_cell_format'].set_font_name('Kanit')

        formats['head_sub_cell_format_warp'] = workbook.add_format({
            'align': 'center',
            'bold': True,
            'top': 1,
        })
        formats['head_sub_cell_format_warp'].set_font_size(9)
        formats['head_sub_cell_format_warp'].set_align('vcenter')
        formats['head_sub_cell_format_warp'].set_font_name('Kanit')
        formats['head_sub_cell_format_warp'].set_text_wrap()

        formats['data_cell_format_left_cus'] = workbook.add_format({
            'align': 'left',
            'border': False,
        })
        formats['data_cell_format_left_cus'].set_font_size(9)
        formats['data_cell_format_left_cus'].set_align('vcenter')
        formats['data_cell_format_left_cus'].set_font_name('Kanit')

        formats['border_format_buttom'] = workbook.add_format({
            'bottom': 1,
        })

        formats['head_sub_cell_format_cus'] = workbook.add_format({
            'align': 'center',
            'bold': True,
            'bottom': 1,
        })
        formats['head_sub_cell_format_cus'].set_font_size(9)
        formats['head_sub_cell_format_cus'].set_align('vcenter')
        formats['head_sub_cell_format_cus'].set_font_name('Kanit')
        formats['head_sub_cell_format_cus'].set_bottom(1)

        formats['top_cell_format'] = workbook.add_format({
            'bold': True,
            'align': 'left',
            'border': True
        })
        formats['top_cell_format'].set_font_size(16)
        formats['top_cell_format'].set_align('vcenter')
        
        formats['date_cell_format'] = workbook.add_format({
            'align': 'left',
            'border': True,
        })
        formats['date_cell_format'].set_font_size(12)
        formats['date_cell_format'].set_align('vcenter')

        formats['data_cell_number_format'] = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'border': False,
        })
        formats['data_cell_number_format'].set_font_size(9)
        formats['data_cell_number_format'].set_align('vcenter')

        formats['head_cell_format'] = workbook.add_format({
            'align': 'center',
            'border': True,
            'bg_color': '#A8A9E3'
        })
        formats['head_cell_format'].set_font_size(12)
        formats['head_cell_format'].set_align('vcenter')
        
        formats['data_cell_format'] = workbook.add_format({
            'border': True,
            'align': 'top'
        })

        formats['format_footerC_bold2_2_2'] = workbook.add_format({'align': 'center', 'bottom': True, 'left': True, 'right': True})
        formats['format_footerC_bold2_2_3'] = workbook.add_format({'align': 'center', 'left': True, 'right': True})
        formats['format_footerC_bold2_2_3'].set_font_size(11)

        formats['data_cell_format_left'] = workbook.add_format({
            'align': 'left',
            'border': False,
            'text_wrap': True,
        })
        formats['data_cell_format_left'].set_font_size(9)
        formats['data_cell_format_left'].set_align('vcenter')

        return formats

    def _setup_worksheet_headers(self, sheet, formats):
        """Setup worksheet headers and column widths"""
        sheet.merge_range('A1:U1', 'รายงานซื้อขายระหว่างกัน', formats['top_cell_format'])
        sheet.merge_range('A2:U2', 'Saeng Charoen Group', formats['top_cell_format'])
        sheet.set_row(0, 20)
        sheet.set_row(1, 15)
        sheet.set_row(2, 15)
        
        row = 4
        headers = [
            'Item Id', 'Item Name', 'Sales Order', 'Invoice', 'SPE Invoice',
            'Document Date', 'Pool', 'Incl. Tax', 'ราคาตั้ง', 'ราคาซื้อ IC-P',
            'ราคาขาย IC-S', 'IC-S Remark', 'Return Cost', 'Cost Group', 'จำนวน',
            'Unit', 'Sales Price', 'Disc. %', 'Disc. Amount', 'รวมภาษี',
            'ก่อนVat', 'ต่อหน่วย', 'Vat/หน่วย', 'รวมVat/หน่วย', 'ต่อหน่วย/Cost Group'
        ]
        
        for col, header in enumerate(headers):
            sheet.write(row, col, header, formats['head_cell_format'])

        column_widths = {
            0: 20, 1: 30, 2: 15, 3: 15, 4: 15, 5: 15, 6: 15, 7: 25, 8: 15, 9: 15,
            10: 15, 11: 20, 12: 15, 13: 15, 14: 15, 15: 15, 16: 15, 17: 15, 18: 15,
            19: 15, 20: 15, 21: 15, 22: 15, 23: 15, 24: 20
        }
        for col, width in column_widths.items():
            sheet.set_column(col, col, width)

    def _should_include_line(self, line, tax_filter):
        """Check if line should be included based on tax filter"""
        if not tax_filter or tax_filter == 'all':
            return True
            
        vat_amount = line.tax_id.amount if line.tax_id else 0
        
        if tax_filter == 'non_vat' and vat_amount == 0:
            return True
        elif tax_filter == 'included' and vat_amount > 0 and line.tax_id.price_include:
            return True
        elif tax_filter == 'vat_ex' and vat_amount > 0 and not line.tax_id.price_include:
            return True
            
        return False

    def _write_data_to_sheet(self, sheet, formats, so_id_ic, so_id_so, specific_product_id=None, tax_filter=None):
        """Write data to worksheet"""
        row = 4
        
        # Process IC transactions
        for so in so_id_ic:
            for line in so.order_line:
                if line.product_id.type != "service":
                    # If specific product is set, only process that product
                    if specific_product_id and line.product_id.id != specific_product_id:
                        continue
                    
                    # Apply tax filter
                    if not self._should_include_line(line, tax_filter):
                        continue
                        
                    row += 1
                    self._write_line_data(sheet, formats, line, so, "IC", row)

        # Process SO transactions
        for so in so_id_so:
            for line in so.order_line:
                if line.product_id.type != "service":
                    # If specific product is set, only process that product
                    if specific_product_id and line.product_id.id != specific_product_id:
                        continue
                    
                    # Apply tax filter
                    if not self._should_include_line(line, tax_filter):
                        continue
                        
                    row += 1
                    self._write_line_data(sheet, formats, line, so, "SO", row)
        
        return row

    def _write_line_data(self, sheet, formats, line, so, pool_type, row):
        """Write individual line data to sheet"""
        invoice_line = line.invoice_lines
        invoice_name = ""
        spe_invoice = ""
        invoice_date = ""

        if len(invoice_line) == 1:
            invoice_line = invoice_line
            invoice_name = invoice_line.move_id.name
            if invoice_line.move_id.form_no:
                spe_invoice = invoice_line.move_id.form_no
            if invoice_line.move_id.invoice_date:
                invoice_date = str(invoice_line.move_id.invoice_date.strftime('%d-%m-%y'))
        elif len(invoice_line) > 1:
            invoice_line = invoice_line[0]
            invoice_name = invoice_line.move_id.name
            if invoice_line.move_id.form_no:
                spe_invoice = invoice_line.move_id.form_no
            if invoice_line.move_id.invoice_date:
                invoice_date = str(invoice_line.move_id.invoice_date.strftime('%d-%m-%y'))

        # Get pricelist item based on pool type
        if pool_type == "IC":
            price_list_item = self.env['product.pricelist.item'].search([
                ('pricelist_id','=',so.pricelist_id.id),
                ('product_id','=',line.product_id.id)
            ])
        else:  # SO
            price_list_item = self.env['product.pricelist.item'].search([
                ('pricelist_id.inter_company_transactions','=',True),
                ('product_id','=',line.product_id.id)
            ])

        fixed_price = 0
        ic_s_remark = ""
        cost_price = 0
        discount = ""
        dis_price = 0

        if price_list_item:
            fixed_price = price_list_item.fixed_price
            ic_s_remark = "Net Price:"+ str(price_list_item.net_price) + "\nFixed Price:" + str(price_list_item.fixed_price) + "\nDiscount:" + str(price_list_item.triple_discount) + "\nPrice:" + str(price_list_item.dis_price) + "\nCost Price:" + str(price_list_item.pricelist_cost_price)
            cost_price = price_list_item.pricelist_cost_price
            if price_list_item.triple_discount:
                discount = price_list_item.triple_discount
            dis_price = price_list_item.dis_price

        fiscal_position_name = ""
        if so.fiscal_position_id:
            fiscal_position_name = so.fiscal_position_id.name

        vat_amount = line.tax_id.amount if line.tax_id else 0
        unit_price_non_vat = line.price_subtotal/line.product_uom_qty if line.product_uom_qty else 0
        unit_vat = unit_price_non_vat * vat_amount / 100
        cost_group = line.product_id.cost_group
        if cost_group == 0:
            unit_by_group = 0
        else:
            unit_by_group = unit_price_non_vat/cost_group

        # Write data to sheet
        sheet.write(row,0, line.product_id.default_code, formats['data_cell_format_left'])
        sheet.write(row,1, line.product_id.name, formats['data_cell_format_left'])
        sheet.write(row,2, so.name, formats['data_cell_format_left'])
        sheet.write(row,3, invoice_name, formats['data_cell_format_left'])
        sheet.write(row,4, spe_invoice, formats['data_cell_format_left'])
        sheet.write(row,5, invoice_date, formats['data_cell_format_left'])
        sheet.write(row,6, pool_type, formats['data_cell_format_left'])
        sheet.write(row,7, fiscal_position_name, formats['data_cell_format_left'])
        sheet.write(row,8, fixed_price, formats['data_cell_number_format'])
        sheet.write(row,9, fixed_price, formats['data_cell_number_format'])
        sheet.write(row,10, fixed_price, formats['data_cell_number_format'])
        sheet.write(row,11, ic_s_remark, formats['data_cell_format_left'])
        sheet.write(row,12, cost_price, formats['data_cell_number_format'])
        sheet.write(row,13, line.product_id.cost_group, formats['data_cell_number_format'])
        sheet.write(row,14, line.product_uom_qty, formats['data_cell_number_format'])
        sheet.write(row,15, line.product_uom.name, formats['data_cell_format_left'])
        sheet.write(row,16, fixed_price, formats['data_cell_number_format'])
        sheet.write(row,17, discount, formats['data_cell_format_left'])
        sheet.write(row,18, dis_price, formats['data_cell_number_format'])
        sheet.write(row,19, line.price_total, formats['data_cell_number_format'])
        sheet.write(row,20, line.price_subtotal, formats['data_cell_number_format'])
        sheet.write(row,21, unit_price_non_vat, formats['data_cell_number_format'])
        sheet.write(row,22, unit_vat, formats['data_cell_number_format'])
        sheet.write(row,23, (unit_price_non_vat + unit_vat), formats['data_cell_number_format'])
        
        if pool_type == "IC":
            sheet.write(row,24, unit_by_group, formats['data_cell_number_format'])
        else:
            sheet.write(row,24, '', formats['data_cell_format_left'])