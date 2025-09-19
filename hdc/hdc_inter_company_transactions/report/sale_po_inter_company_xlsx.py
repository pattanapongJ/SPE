# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
import pytz
import datetime
from datetime import datetime, date, time, timedelta

from decimal import Decimal, ROUND_HALF_UP
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError, except_orm

class SalePOInterCompanyXlsx(models.AbstractModel):
    _name = 'report.sale_po_inter_company_xlsx'
    _description = 'report.sale_po_inter_company_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _get_tax_filter_domain(self, tax_filter):
        """Get domain filter based on tax selection"""
        if tax_filter == 'non_vat':
            return [('tax_id', '=', False)]
        elif tax_filter == 'included':
            return [('tax_id.price_include', '=', True)]
        elif tax_filter == 'vat_ex':
            return [('tax_id.price_include', '=', False), ('tax_id', '!=', False)]
        else:  # 'all' or no filter
            return []

    def _get_base_domain(self, date_from, date_to, company_ids=None, product_ids=None, tax_filter=None):
        """Get base domain for filtering records"""
        domain = [
            ('date_order', '<=', date_to), 
            ('date_order', '>=', date_from)
        ]
        
        # Add customer filter
        if company_ids:
            domain.append(('partner_id', 'in', company_ids.sale_contact_id.ids))
        
        return domain

    def _get_so_records(self, objects):
        """Get SO records based on filters"""
        date_from = objects.from_date
        date_to = objects.to_date
        
        # Base domain for SO with inter-company transactions
        domain_ic = self._get_base_domain(date_from, date_to, objects.company_ids)
        domain_ic.append(('type_id.inter_company_transactions', '=', True))
        
        # Base domain for regular SO with inter-company flag
        domain_so = self._get_base_domain(date_from, date_to, objects.company_ids)
        domain_so.extend([
            ('type_id.inter_company_transactions', '=', False),
            ('inter_so_company', '!=', False)
        ])
        
        so_ic_records = self.env['sale.order'].search(domain_ic)
        so_regular_records = self.env['sale.order'].search(domain_so)
        
        return so_ic_records, so_regular_records

    def _get_po_records(self, so_records):
        """Get PO records based on SO source documents"""
        po_records = self.env['purchase.order']
        
        for so in so_records:
            # Find PO with matching source document and inter-company transaction type
            po_domain = [
                ('origin', '=', so.name),
                ('order_type.inter_company_transactions', '=', True)
            ]
            po_found = self.env['purchase.order'].search(po_domain)
            po_records |= po_found
            
        return po_records

    def _filter_lines_by_criteria(self, lines, objects, line_type="so"):
        """Filter order lines based on product and tax criteria"""
        filtered_lines = lines.filtered(lambda l: l.product_id.type != "service")
        
        # Filter by product
        if objects.product_ids:
            filtered_lines = filtered_lines.filtered(lambda l: l.product_id in objects.product_ids)
        
        # Filter by tax
        if objects.tax and objects.tax != 'all':
            if objects.tax == 'non_vat':
                if line_type == "so":
                    filtered_lines = filtered_lines.filtered(lambda l: not l.tax_id)
                else:  # PO
                    filtered_lines = filtered_lines.filtered(lambda l: not l.taxes_id)
            elif objects.tax == 'included':
                if line_type == "so":
                    filtered_lines = filtered_lines.filtered(lambda l: l.tax_id and l.tax_id.price_include)
                else:  # PO
                    filtered_lines = filtered_lines.filtered(lambda l: l.taxes_id and any(tax.price_include for tax in l.taxes_id))
            elif objects.tax == 'vat_ex':
                if line_type == "so":
                    filtered_lines = filtered_lines.filtered(lambda l: l.tax_id and not l.tax_id.price_include)
                else:  # PO
                    filtered_lines = filtered_lines.filtered(lambda l: l.taxes_id and not any(tax.price_include for tax in l.taxes_id))
        
        return filtered_lines

    def _create_worksheet_formats(self, workbook):
        """Create all worksheet formats"""
        formats = {}
        
        # Header formats
        formats['top_cell_format'] = workbook.add_format({
            'bold': True,
            'align': 'left',
            'border': True
        })
        formats['top_cell_format'].set_font_size(16)
        formats['top_cell_format'].set_align('vcenter')
        
        formats['head_cell_format'] = workbook.add_format({
            'align': 'center',
            'border': True,
            'bg_color': '#A8A9E3'
        })
        formats['head_cell_format'].set_font_size(12)
        formats['head_cell_format'].set_align('vcenter')
        
        # Data formats
        formats['data_cell_format_left'] = workbook.add_format({
            'align': 'left',
            'border': False,
            'text_wrap': True,
        })
        formats['data_cell_format_left'].set_font_size(9)
        formats['data_cell_format_left'].set_align('vcenter')
        
        formats['data_cell_number_format'] = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'border': False,
        })
        formats['data_cell_number_format'].set_font_size(9)
        formats['data_cell_number_format'].set_align('vcenter')
        
        return formats

    def _write_headers(self, sheet, formats):
        """Write headers to worksheet"""
        # Title headers
        sheet.merge_range('A1:Y1', 'รายงานซื้อขายระหว่างกัน', formats['top_cell_format'])
        sheet.merge_range('A2:Y2', 'Saeng Charoen Group', formats['top_cell_format'])
        sheet.set_row(0, 20)
        sheet.set_row(1, 15)
        sheet.set_row(2, 15)
        
        # Column headers
        headers = [
            'Item Id', 'Item Name', 'Sales Order', 'Purchase Order', 'Invoice', 
            'SPE Invoice', 'Document Date', 'Pool', 'Incl. Tax', 'ราคาตั้ง', 
            'ราคาซื้อ IC-P', 'ราคาขาย IC-S', 'IC-S Remark', 'Return Cost', 
            'Cost Group', 'จำนวน', 'Unit', 'Sales Price', 'Disc. %', 
            'Disc. Amount', 'รวมภาษี', 'ก่อนVat', 'ต่อหน่วย', 'Vat/หน่วย', 
            'รวมVat/หน่วย', 'ต่อหน่วย/Cost Group'
        ]
        
        row = 4
        for col, header in enumerate(headers):
            sheet.write(row, col, header, formats['head_cell_format'])
        
        # Set column widths
        column_widths = {
            0: 20, 1: 30, 2: 15, 3: 15, 4: 15, 5: 15, 6: 15, 7: 25, 8: 15, 
            9: 15, 10: 15, 11: 20, 12: 15, 13: 15, 14: 15, 15: 15, 16: 15, 
            17: 15, 18: 15, 19: 15, 20: 15, 21: 15, 22: 15, 23: 15, 24: 15, 25: 20
        }
        for col, width in column_widths.items():
            sheet.set_column(col, col, width)
        
        return row + 1

    def _write_so_line_data(self, sheet, line, so, row, formats, pool_type="IC"):
        """Write SO line data to worksheet"""
        # Get invoice information
        invoice_line = line.invoice_lines
        invoice_name = ""
        spe_invoice = ""
        invoice_date = ""
        
        if invoice_line:
            invoice_line = invoice_line[0] if len(invoice_line) > 1 else invoice_line
            invoice_name = invoice_line.move_id.name
            if invoice_line.move_id.form_no:
                spe_invoice = invoice_line.move_id.form_no
            if invoice_line.move_id.invoice_date:
                invoice_date = str(invoice_line.move_id.invoice_date.strftime('%d-%m-%y'))
        
        # Get price list information
        price_list_domain = [('product_id', '=', line.product_id.id)]
        if pool_type == "IC":
            price_list_domain.append(('pricelist_id', '=', so.pricelist_id.id))
        else:
            price_list_domain.append(('pricelist_id.inter_company_transactions', '=', True))
        
        price_list_item = self.env['product.pricelist.item'].search(price_list_domain)
        
        fixed_price = 0
        ic_s_remark = ""
        cost_price = 0
        discount = ""
        dis_price = 0
        
        if price_list_item:
            fixed_price = price_list_item.fixed_price
            ic_s_remark = f"Net Price:{price_list_item.net_price}\nFixed Price:{price_list_item.fixed_price}\nDiscount:{price_list_item.triple_discount}\nPrice:{price_list_item.dis_price}\nCost Price:{price_list_item.pricelist_cost_price}"
            cost_price = price_list_item.pricelist_cost_price
            if price_list_item.triple_discount:
                discount = price_list_item.triple_discount
            dis_price = price_list_item.dis_price
        
        # Get fiscal position
        fiscal_position_name = ""
        if so.fiscal_position_id:
            fiscal_position_name = so.fiscal_position_id.name
        
        # Calculate VAT and prices
        vat_amount = line.tax_id.amount if line.tax_id else 0
        unit_price_non_vat = line.price_subtotal / line.product_uom_qty if line.product_uom_qty else 0
        unit_vat = unit_price_non_vat * vat_amount / 100
        cost_group = line.product_id.cost_group
        unit_by_group = unit_price_non_vat / cost_group if cost_group else 0
        
        # Write data to sheet
        data = [
            line.product_id.default_code or "",
            line.product_id.name or "",
            so.name or "",
            "",  # PO will be filled separately
            invoice_name,
            spe_invoice,
            invoice_date,
            pool_type,
            fiscal_position_name,
            fixed_price,
            fixed_price,
            fixed_price,
            ic_s_remark,
            cost_price,
            line.product_id.cost_group,
            line.product_uom_qty,
            line.product_uom.name if line.product_uom else "",
            fixed_price,
            discount,
            dis_price,
            line.price_total,
            line.price_subtotal,
            unit_price_non_vat,
            unit_vat,
            unit_price_non_vat + unit_vat,
            unit_by_group if pool_type == "IC" else ""
        ]
        
        for col, value in enumerate(data):
            if isinstance(value, (int, float)) and col > 8:  # Numeric columns
                sheet.write(row, col, value, formats['data_cell_number_format'])
            else:
                sheet.write(row, col, value, formats['data_cell_format_left'])

    def _write_po_line_data(self, sheet, line, po, row, formats):
        """Write PO line data to worksheet"""
        # Similar to SO line but for PO data
        # Get invoice information for PO (vendor bills)
        invoice_line = line.invoice_lines if hasattr(line, 'invoice_lines') else []
        invoice_name = ""
        spe_invoice = ""
        invoice_date = ""
        
        if invoice_line:
            invoice_line = invoice_line[0] if len(invoice_line) > 1 else invoice_line
            invoice_name = invoice_line.move_id.name
            if hasattr(invoice_line.move_id, 'form_no') and invoice_line.move_id.form_no:
                spe_invoice = invoice_line.move_id.form_no
            if invoice_line.move_id.invoice_date:
                invoice_date = str(invoice_line.move_id.invoice_date.strftime('%d-%m-%y'))
        
        # Calculate VAT for PO (using taxes_id instead of tax_id)
        vat_amount = 0
        if line.taxes_id:
            vat_amount = line.taxes_id[0].amount if line.taxes_id else 0
        
        unit_price_non_vat = line.price_subtotal / line.product_qty if line.product_qty else 0
        unit_vat = unit_price_non_vat * vat_amount / 100
        
        # Get fiscal position for PO
        fiscal_position_name = ""
        if po.fiscal_position_id:
            fiscal_position_name = po.fiscal_position_id.name
        
        # PO specific data writing logic
        data = [
            line.product_id.default_code or "",
            line.product_id.name or "",
            po.origin or "",  # SO name from origin
            po.name or "",
            invoice_name,
            spe_invoice,
            invoice_date,
            "PO",
            fiscal_position_name,
            line.price_unit,
            line.price_unit,
            line.price_unit,
            "",  # PO remark
            0,  # cost price
            line.product_id.cost_group,
            line.product_qty,
            line.product_uom.name if line.product_uom else "",
            line.price_unit,
            "",  # discount
            0,  # discount amount
            line.price_total,
            line.price_subtotal,
            unit_price_non_vat,
            unit_vat,
            unit_price_non_vat + unit_vat,
            ""  # unit by group
        ]
        
        for col, value in enumerate(data):
            if isinstance(value, (int, float)) and col > 8:
                sheet.write(row, col, value, formats['data_cell_number_format'])
            else:
                sheet.write(row, col, value, formats['data_cell_format_left'])

    def generate_xlsx_report(self, workbook, data, objects):
        date_from = objects.from_date
        date_to = objects.to_date
        
        # Get records based on type selection
        so_ic_records, so_regular_records = self._get_so_records(objects)
        
        # Get PO records if needed
        po_records = self.env['purchase.order']
        if objects.by_type in ['po', 'so_po']:
            all_so_records = so_ic_records | so_regular_records
            po_records = self._get_po_records(all_so_records)
        
        # Create formats
        formats = self._create_worksheet_formats(workbook)
        
        # Group data by product if product filter is applied
        if objects.product_ids:
            for product in objects.product_ids:
                sheet_name = f"{product.default_code or product.name}"[:31]  # Excel sheet name limit
                sheet = workbook.add_worksheet(sheet_name)
                row = self._write_headers(sheet, formats)
                
                # Process SO records for this product
                if objects.by_type in ['so', 'so_po']:
                    # IC Sales Orders
                    for so in so_ic_records:
                        filtered_lines = self._filter_lines_by_criteria(so.order_line, objects, "so")
                        product_lines = filtered_lines.filtered(lambda l: l.product_id == product)
                        
                        for line in product_lines:
                            self._write_so_line_data(sheet, line, so, row, formats, "IC")
                            row += 1
                    
                    # Regular Sales Orders
                    for so in so_regular_records:
                        filtered_lines = self._filter_lines_by_criteria(so.order_line, objects, "so")
                        product_lines = filtered_lines.filtered(lambda l: l.product_id == product)
                        
                        for line in product_lines:
                            self._write_so_line_data(sheet, line, so, row, formats, "SO")
                            row += 1
                
                # Process PO records for this product
                if objects.by_type in ['po', 'so_po']:
                    for po in po_records:
                        filtered_lines = self._filter_lines_by_criteria(po.order_line, objects, "po")
                        product_lines = filtered_lines.filtered(lambda l: l.product_id == product)
                        
                        for line in product_lines:
                            self._write_po_line_data(sheet, line, po, row, formats)
                            row += 1
        
        else:
            # Single sheet for all data
            report_name = "รายงานซื้อขายระหว่างกัน"
            sheet = workbook.add_worksheet(report_name)
            row = self._write_headers(sheet, formats)
            
            # Process all SO records
            if objects.by_type in ['so', 'so_po']:
                # IC Sales Orders
                for so in so_ic_records:
                    filtered_lines = self._filter_lines_by_criteria(so.order_line, objects, "so")
                    
                    for line in filtered_lines:
                        self._write_so_line_data(sheet, line, so, row, formats, "IC")
                        row += 1
                
                # Regular Sales Orders
                for so in so_regular_records:
                    filtered_lines = self._filter_lines_by_criteria(so.order_line, objects, "so")
                    
                    for line in filtered_lines:
                        self._write_so_line_data(sheet, line, so, row, formats, "SO")
                        row += 1
            
            # Process all PO records
            if objects.by_type in ['po', 'so_po']:
                for po in po_records:
                    filtered_lines = self._filter_lines_by_criteria(po.order_line, objects, "po")
                    
                    for line in filtered_lines:
                        self._write_po_line_data(sheet, line, po, row, formats)
                        row += 1