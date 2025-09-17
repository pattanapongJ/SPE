# -*- coding: utf-8 -*-

import time

from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class SaleQuotationsReport(models.AbstractModel):
    _name = 'report.hdc_inventory_general_report.hdc_sale_order_report'
    _description = 'Sale Quotations Report template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)

        order_lines = self.env['sale.order.line'].search([('order_id', 'in', docs.ids)], order='sequence')
        
        set_total_discount = 0.0
        for doc in docs:
            for line in doc.order_line:
                set_total_discount += line.discount_config
        report_values = {
            'doc_ids': docids,
            'doc_model': 'mrp.production',
            'docs': docs,
            'order_lines': order_lines,
            'total_discount': set_total_discount,
        }
        return report_values
    
class ReportInterTransfer(models.AbstractModel):
    _name = 'report.hdc_inventory_general_report.hdc_inter_report'
    _description = 'Report Inter Transfer'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        
        docs = self.env['stock.picking'].browse(docids)
        
        receipt_inter_transfer = self.env['stock.picking'].search([('origin', '=', docs.name) , ('picking_type_code', '=', "incoming")])
        lot_ids = receipt_inter_transfer.move_line_ids.filtered(lambda ml: ml.lot_id)
        delivery_inter_transfer = self.env['stock.picking'].search([('origin', '=', docs.name) , ('picking_type_code', '=', "outgoing")])
        
        report_values = {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'receipt_inter': receipt_inter_transfer,
            'delivery_inter': delivery_inter_transfer,
        }
        return report_values

class ReportInterTranferLS(models.AbstractModel):
    _name = 'report.hdc_inventory_general_report.hdc_tranfers_ls_report'
    _description = 'Report Inter Transfer'

    @api.model
    def _get_report_values(self, docids, data=None):
        # ดึงเวลาปัจจุบัน
        now = datetime.now() + timedelta(hours=7)
        current_date = now.strftime('%Y-%m-%d')
        current_time = now.strftime('%H:%M:%S')

        docs = self.env['stock.picking'].browse(docids)
        receipt_inter_transfer = self.env['stock.picking'].search([('origin', '=', docs.name) , ('picking_type_code', '=', "incoming") , ('backorder_id', '=', False)],limit=1)
        delivery_inter_transfer = self.env['stock.picking'].search([('origin', '=', docs.name) , ('picking_type_code', '=', "outgoing") , ('backorder_id', '=', False)],limit=1)
        demand_count = 0.0
        product_location_map = []
        for doc in docs:
            for move in doc.move_ids_without_package:
                product_id = move.product_id.id
                for delivery_move in delivery_inter_transfer.move_ids_without_package:
                    if delivery_move.product_id.id == product_id and delivery_move.move_line_nosuggest_ids:
                        first_location_id = delivery_move.move_line_nosuggest_ids[0].location_id.display_name
                        first_location_name = first_location_id.split('/')[0]
                        if first_location_id:
                            # เช็คว่ามีข้อมูลซ้ำใน product_location_map หรือไม่
                            if (product_id, first_location_id) not in product_location_map:
                                # product_location_map.append((product_id, first_location_id))
                                data = {
                                    "product_id": product_id,
                                    "location_id": first_location_name,
                                }
                                product_location_map.append(data)
        
        for move in receipt_inter_transfer:
            if move.state != 'done':
                for line in move.move_ids_without_package:
                    demand_count += line.product_uom_qty
        
        for data in product_location_map:
            moves_to_update = docs.move_ids_without_package.filtered(lambda line: line.product_id.id == data['product_id'])
            for move in moves_to_update:
                move.write({"delivery_location_id": data['location_id']})

        return {
            'docs': self.env['stock.picking'].browse(docids),
            'current_date': current_date,
            'current_time': current_time,
            'demand_count': demand_count,
            'product_location_map': product_location_map,
        }

