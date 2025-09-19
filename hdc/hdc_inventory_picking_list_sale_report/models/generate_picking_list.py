# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
# from BeautifulSoup import BeautifulSoup as BSHTML

class PickingList(models.Model):
    _inherit = 'picking.lists'
    _description = "Picking Lists"

    barcode_date = fields.Date(string="Barcode Date")

    def check_stock_not_get(self,data):
        check = 0
        if "NG" not in data.location_id.complete_name:
            check = 1
        if "Lost" not in data.location_id.complete_name:
            check = 1
        if "RP" not in data.location_id.complete_name:
            check = 1
        if "Inter Tranfer" not in data.location_id.complete_name:
            check = 1
        return check
    def get_stock_24A(self,data):
        location_list = self.env['stock.quant'].search([('product_id','=', data.product_id.id),('location_id.usage','=','internal')])
        total_available_quantity = 0
        for rec in location_list:
            if "24A" in rec.location_id.complete_name:
                if self.check_stock_not_get(rec) == 1:
                    total_available_quantity = total_available_quantity + rec.available_quantity
        return total_available_quantity
    def get_stock_24B(self,data):
        location_list = self.env['stock.quant'].search([('product_id','=', data.product_id.id),('location_id.usage','=','internal')])
        total_available_quantity = 0
        for rec in location_list:
            if "24B" in rec.location_id.complete_name:
                if self.check_stock_not_get(rec) == 1:
                    total_available_quantity = total_available_quantity + rec.available_quantity
        return total_available_quantity
    def get_stock_other(self,data):
        location_list = self.env['stock.quant'].search([('product_id','=', data.product_id.id),('location_id.usage','=','internal')])
        total_available_quantity = 0
        for rec in location_list:
            if self.check_stock_not_get(rec) == 1:
                total_available_quantity = total_available_quantity + rec.available_quantity
        total_available_quantity = total_available_quantity - (self.get_stock_24A(data)+self.get_stock_24B(data))
        return total_available_quantity

    def print_pk_list(self):
        self.ensure_one()
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.picking.list.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.state},
            }
    
class PickingListLine(models.Model):
    _inherit = 'picking.lists.line'
    _description = "Picking List Line"

    qty_all_stock = fields.Float("All Stock", digits = 'Product Unit of Measure',compute = "_compute_qty_all_stock")

    def get_stock_warehouse(self,warehose):
        location_list = self.env['stock.quant'].search([('product_id','=', self.product_id.id),('location_id.usage','=','internal')])
        total_available_quantity = 0
        for rec in location_list:
            if warehose and rec.location_id.complete_name:
                if warehose in rec.location_id.complete_name:
                    if self.picking_lists.check_stock_not_get(rec) == 1:
                        total_available_quantity = total_available_quantity + rec.available_quantity
        return total_available_quantity
    
    def _compute_qty_all_stock(self):
        for rec in self:
            location_list = self.env['stock.quant'].search([('product_id','=', rec.product_id.id),('location_id.usage','=','internal')])
            total_available_quantity = 0
            for rec2 in location_list:
                if rec.picking_lists.check_stock_not_get(rec2) == 1:
                    total_available_quantity = total_available_quantity + rec2.available_quantity
            total_available_quantity = total_available_quantity - (rec.get_stock_warehouse(rec.picking_lists.warehouse_id.name))
            rec.qty_all_stock = total_available_quantity


