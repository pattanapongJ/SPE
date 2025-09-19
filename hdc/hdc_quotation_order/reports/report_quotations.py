# -*- coding: utf-8 -*-

import time
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta

class ReportProformaQENDis(models.AbstractModel):
    _name = 'report.hdc_quotation_order.hdc_proforma_en_dis_report'
    _description = 'Report PROFORMA EN Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("quotation_id", False)
        docs = self.env['quotation.order'].browse(ids)
        type = data.get("type", False)
        product_design = data.get("product_design", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'quotation.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
            'product_design': product_design,
        }
        return report_values

class ReportProformaQENNODis(models.AbstractModel):
    _name = 'report.hdc_quotation_order.hdc_proforma_en_no_dis_report'
    _description = 'Report PROFORMA EN Dis'
        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("quotation_id", False)
        docs = self.env['quotation.order'].browse(ids)
        type = data.get("type", False)
        product_design = data.get("product_design", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'quotation.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
            'product_design': product_design,
        }
        return report_values

class ReportQuotationTHDis(models.AbstractModel):
    _name = 'report.hdc_quotation_order.hdc_quotation_th_dis_report'
    _description = 'Report Quotation TH Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("quotation_id", False)
        docs = self.env['quotation.order'].browse(ids)
        type = data.get("type", False)
        product_design = data.get("product_design", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'quotation.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
            'product_design': product_design,
        }
        return report_values

class ReportQuotationDTHDis(models.AbstractModel):
    _name = 'report.hdc_quotation_order.hdc_quotation_d_th_dis_report'
    _description = 'Report Quotation Debt TH Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("quotation_id", False)
        docs = self.env['quotation.order'].browse(ids)
        type = data.get("type", False)
        product_design = data.get("product_design", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'quotation.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
            'product_design': product_design,
        }
        return report_values

class ReportQuotationTHNoDis(models.AbstractModel):
    _name = 'report.hdc_quotation_order.hdc_quotation_th_no_dis_report'
    _description = 'Report Quotation TH No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("quotation_id", False)
        docs = self.env['quotation.order'].browse(ids)
        type = data.get("type", False)
        product_design = data.get("product_design", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'quotation.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
            'product_design': product_design,
        }
        return report_values
    
class ReportQuotationDTHNoDis(models.AbstractModel):
    _name = 'report.hdc_quotation_order.hdc_quotation_d_th_no_dis_report'
    _description = 'Report Quotation Debt TH No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("quotation_id", False)
        docs = self.env['quotation.order'].browse(ids)
        type = data.get("type", False)
        product_design = data.get("product_design", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'quotation.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
            'product_design': product_design,
        }
        return report_values

class ReportQuotationENDis(models.AbstractModel):
    _name = 'report.hdc_quotation_order.hdc_quotation_en_dis_report'
    _description = 'Report Quotation EN Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("quotation_id", False)
        docs = self.env['quotation.order'].browse(ids)
        type = data.get("type", False)
        product_design = data.get("product_design", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'quotation.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
            'product_design': product_design,
        }
        return report_values

class ReportQuotationENNoDis(models.AbstractModel):
    _name = 'report.hdc_quotation_order.hdc_quotation_en_no_dis_report'
    _description = 'Report Quotation EN No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("quotation_id", False)
        docs = self.env['quotation.order'].browse(ids)
        type = data.get("type", False)
        product_design = data.get("product_design", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'quotation.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
            'product_design': product_design,
        }
        return report_values

class ReportQuotationBo(models.AbstractModel):
    _name = 'report.hdc_quotation_order.hdc_quotation_project_bo'
    _description = 'Report Quotation Project Bo'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        
        docs = self.env['quotation.order'].browse(docids)

        # sale_id = self.env['sale.order'].search([('quotation_id', '=', self.id)])
        transfer24_dict = {}
        transfer_other_dict = {}
        batch_dict = {} #ค้างรับ
        picking_list_dict = {} #ค้างส่ง
        physical_inv_dict = {}

        for doc in docs:
            for line in doc.quotation_line:
                product_id = line.product_id.id
                transfer24_total = 0
                transfer_other_total = 0
                batch_total = 0
                picking_list_total = 0
                physical_inv_total = 0
                in_amount = 0
                out_amount = 0

                # ค้นหา Stock Picking ที่มีเงื่อนไขตามที่กำหนด
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

        report_values = {
            'doc_ids': docids,
            'doc_model': 'quotation.order',
            'docs': docs,
            'transfer24': transfer24_dict,
            'transfer_other': transfer_other_dict,
            'batch': batch_dict,
            'picking_list': picking_list_dict,
            'physical_inv': physical_inv_dict,
        }
        return report_values

class ReportQuotationDepart(models.AbstractModel):
    _name = 'report.hdc_quotation_order.hdc_quotation_project_depart'
    _description = 'Report Quotation Project Department'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        
        docs = self.env['quotation.order'].browse(docids)

        # sale_id = self.env['sale.order'].search([('quotation_id', '=', self.id)])
        transfer24_dict = {}
        transfer_other_dict = {}
        batch_dict = {} #ค้างรับ
        picking_list_dict = {} #ค้างส่ง
        physical_inv_dict = {}

        for doc in docs:
            for line in doc.quotation_line:
                product_id = line.product_id.id
                transfer24_total = 0
                transfer_other_total = 0
                batch_total = 0
                picking_list_total = 0
                physical_inv_total = 0
                in_amount = 0
                out_amount = 0

                # ค้นหา Stock Picking ที่มีเงื่อนไขตามที่กำหนด
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

        report_values = {
            'doc_ids': docids,
            'doc_model': 'quotation.order',
            'docs': docs,
            'transfer24': transfer24_dict,
            'transfer_other': transfer_other_dict,
            'batch': batch_dict,
            'picking_list': picking_list_dict,
            'physical_inv': physical_inv_dict,
        }
        return report_values