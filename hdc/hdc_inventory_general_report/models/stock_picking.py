from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
    
    
class Followers(models.Model):
   _inherit = 'mail.followers'

   @api.model
   def create(self, vals):
        if 'res_model' in vals and 'res_id' in vals and 'partner_id' in vals:
            dups = self.env['mail.followers'].search([('res_model', '=',vals.get('res_model')),
                                           ('res_id', '=', vals.get('res_id')),
                                           ('partner_id', '=', vals.get('partner_id'))])
            if len(dups):
                for p in dups:
                    p.unlink()
        return super(Followers, self).create(vals)
    
class StockMove(models.Model):
    _inherit = 'stock.move'

    shortage_qty = fields.Float(string="Shortage QTY", compute="_compute_shortage_overage_qty", store=True)
    overage_qty = fields.Float(string="Overage QTY", compute="_compute_shortage_overage_qty", store=True)

    @api.depends('purchase_line_id.product_qty', 'purchase_line_id.qty_received')
    def _compute_shortage_overage_qty(self):
        for move in self:
            po_qty = move.purchase_line_id.product_qty if move.purchase_line_id else 0.0
            received_qty = move.purchase_line_id.qty_received if move.purchase_line_id else 0.0

            move.shortage_qty = po_qty - received_qty if po_qty > received_qty else 0.0
            move.overage_qty = received_qty - po_qty if received_qty > po_qty else 0.0

    
class Picking(models.Model):
    _inherit = 'stock.picking'
    
    addition_operation_types = fields.Many2one(related = 'picking_type_id.addition_operation_types')
    addition_operation_types_code = fields.Char(related='addition_operation_types.code')
    print_llk_status = fields.Selection([
        ('no', 'Not Print'),
        ('print', 'Print'),
    ], string="Print LLK Status",default='no')

    def print_llk_status_change(self):
        self.print_llk_status = 'print'
        return 'print'

    def check_iso_name(self, check_iso):
        for purchase in self:
            check_model = self.env["ir.actions.report"].search([('model', '=', 'stock.picking'),('report_name', '=', check_iso)], limit=1)
            if check_model:
                return check_model.iso_name
            else:
                return "-"
    
    def do_receipt_print_picking(self):

        self.ensure_one()
        return {
                "name": "Receipt Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.receipt.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_picking_id": self.id},
            }
             
    def do_internal_tranfer_print_picking(self):
        return self.env.ref('hdc_inventory_general_report.internal_tranfer_inventory_report_view').report_action(self)
    
    def do_delivery_print_picking(self):
                    
        return self.env.ref('hdc_inventory_general_report.delivery_inventory_report_view').report_action(self)
    
    def do_inter_tranfer_print_picking(self):
        self.ensure_one()
        return {
                "name": "Inter Tranfers Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.inter.tranfers.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_picking_id": self.id},
            }


    def do_requestion_print_picking(self):
        self.ensure_one()
        return {
                "name": "Borrow Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.borrow.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_picking_id": self.id},
            }

    def do_return_customer_print_picking(self):
        return self.env.ref('hdc_inventory_general_report.return_cus_inventory_report_view').report_action(self)
    
    def print_pk_list(self):
        self.ensure_one()
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.inventory.picking.list.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.state},
            }
    
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

    def check_stock_warehouse_not_get(self,data):
        check = 0
        if "NG" not in data.location_id.complete_name:
            check += 1
        if "Lost" not in data.location_id.complete_name:
            check += 1
        if "RP" not in data.location_id.complete_name:
            check += 1
        if "Inter Transfer" not in data.location_id.complete_name:
            check += 1
        if "BOOTH" not in data.location_id.complete_name:
            check += 1
        if "RG" not in data.location_id.complete_name:
            check += 1
        if "Retail" not in data.location_id.complete_name:
            check += 1
        if "CG" not in data.location_id.complete_name:
            check += 1
        return check
    
    def get_stock_warehouse(self,data,warehouse):
        location_list = self.env['stock.quant'].search([('product_id','=', data.product_id.id),('location_id.usage','=','internal')])
        total_available_quantity = 0
        for rec in location_list:
            if warehouse.name in rec.location_id.complete_name:
                if self.check_stock_warehouse_not_get(rec) == 8:
                    total_available_quantity = total_available_quantity + rec.available_quantity
        return total_available_quantity

    def check_stamp_report(self, check_stamp_report):
        for billing in self:
            check_model = self.env["ir.actions.report"].search([('model', '=', 'stock.picking'),('report_name', '=', check_stamp_report)], limit=1)
            if check_model:
                return check_model.stamp_report
            else:
                return "-"

    def print_sale_borrow(self):
        self.ensure_one()
        return {
                "name": "Borrow Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.borrow.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {
                    "default_picking_id": self.id,
                    "default_is_delivery_note": True,
                },
            }
        # return self.env.ref('hdc_inventory_general_report.inventory_borrow_report_view').report_action(self.id)