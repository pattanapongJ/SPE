# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from werkzeug.urls import url_encode

class BoothConsignUrgentDelivery(models.Model):
    _name = "booth.consign.urgent.delivery"
    _description = "Booth and Consignment Urgent Delivery Transfer"
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string = 'Name', default = lambda self: _('New'), copy = False)
    date = fields.Datetime("Pick Date", default = fields.Datetime.now)
    delivery_date = fields.Datetime("Delivery Date")
    user_employee_id = fields.Many2one('hr.employee', string = 'Responsible', index = True, tracking = 2)
    state = fields.Selection(
        [('in_progress', 'In progress'),('waiting_delivery', 'Waiting Delivery'), ('done', 'Done'), ('cancel', 'Cancelled'), ],
        string = 'Status', readonly = True, default = 'in_progress', tracking = True)

    sale_order_ids = fields.One2many('sale.order','b_c_urgent_delivery_id', string = "Sale Order")

    picking_ids = fields.One2many('stock.picking', 'b_c_urgent_delivery_id', string = 'Transfers', readonly = True, store=True, index=True)
    from_warehouse = fields.Many2one("stock.warehouse", string="To Warehouse")
    to_warehouse = fields.Many2one("stock.warehouse", string = "From Warehouse")
    transit_location = fields.Many2one("stock.location", string="Source Location")
    location_dest_id = fields.Many2one('stock.location', "Transit Location",)
    location_id = fields.Many2one('stock.location', "Destination Location",)
    b_c_urgent_delivery_line = fields.One2many('booth.consign.urgent.delivery.line','b_c_urgent_delivery_id', string = "Product List")
    delivery_check = fields.Boolean('Delivery Check',default=False,compute="_compute_delivery_check")
    receipt_check = fields.Boolean('Receipt Check',default=False,compute="_compute_receipt_check")
    remark = fields.Text(string="Remark", tracking=True,) 
    
    def _update_state(self):
        for rec in self:
            rec.state = "done"
            rec.delivery_date = datetime.now()

    def action_inter(self):
        picking_ids = self.env['stock.picking'].search([('b_c_urgent_delivery_id', '=', self.id)])
        action = {
            'name':"Transfer Delivery & Receipts",
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
        }
        if len(picking_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': picking_ids[0].id,
            })
        else:
            action.update({
                'domain': [('id', 'in', picking_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('b_c_urgent_delivery') or _('New')
        result = super(BoothConsignUrgentDelivery, self).create(vals)
        return result

    def action_cancel(self):
        self.sale_order_ids = False
        for line in self.picking_ids:
            if line.state != 'cancel':
                raise UserError(_("Please cancel Transfer"))
        self.state = 'cancel'

    def action_open_wizard_add_urgent_delivery(self):
        context = {
            'default_b_c_urgent_delivery_id': self.id,
        }
        return {
                'type': 'ir.actions.act_window',
                'name': 'Wizard Add Booth Consignment Urgent Delivery Transfer',
                'res_model': 'wizard.add.booth.consign.urgent.delivery',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    def action_open_wizard_remove_urgent_delivery(self):
        context = {
            'default_b_c_urgent_delivery_id': self.id,
        }
        return {
                'type': 'ir.actions.act_window',
                'name': 'Wizard Remove Booth Consignment Urgent Delivery Transfer',
                'res_model': 'wizard.remove.booth.consign.urgent.delivery',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    @api.onchange('to_warehouse')
    def _onchange_to_warehouse(self):
        self.transit_location = self.to_warehouse.lot_stock_id.id

    @api.onchange('from_warehouse')
    def _onchange_from_warehouse(self):
        self.location_id = self.from_warehouse.lot_stock_id.id
        self.location_dest_id = self.from_warehouse.transit_location.id

    @api.depends('state', 'b_c_urgent_delivery_line')
    def _compute_delivery_check(self):
        for rec in self:
            picking_ids = rec.env['stock.picking'].search([('b_c_urgent_delivery_id', '=', rec.id),('picking_type_id','=',rec.to_warehouse.inter_transfer_delivery.id)])
            if picking_ids:
                rec.delivery_check = True
            else:
                rec.delivery_check = False

    @api.depends('state', 'b_c_urgent_delivery_line')
    def _compute_receipt_check(self):
        for rec in self:
            picking_ids = rec.env['stock.picking'].search([('b_c_urgent_delivery_id', '=', rec.id),('picking_type_id','=',rec.from_warehouse.inter_transfer_receive.id)])
            if picking_ids:
                rec.receipt_check = True
            else:
                rec.receipt_check = False

    def create_delivery(self):
        if self.to_warehouse:
            # OUTGOING ------------
            move_line = []
            company_id = self.env.company.id
            self.state = "waiting_delivery"
            if self.to_warehouse.inter_transfer_delivery :
            # if self.to_warehouse.out_type_id:
                for move in self.b_c_urgent_delivery_line:
                    move_line.append((0, 0, {
                        "product_id": move.product_id.id,
                        "name": move.product_id.name,
                        "product_uom_qty": move.qty,
                        "product_uom": move.product_uom.id,
                        "company_id": company_id,
                        "location_id": self.transit_location.id,
                        "location_dest_id": self.location_dest_id.id,
                        "urgent_pick": move.urgent_pick,
                        "urgent_remain": move.urgent_pick,
                        "urgent_location_ids": move.urgent_location_ids,
                        }))

                picking_out = self.env["stock.picking"].create({
                    "picking_type_id": self.to_warehouse.inter_transfer_delivery.id if self.to_warehouse.inter_transfer_delivery else  self.to_warehouse.out_type_id.id,
                    "b_c_urgent_delivery_id":self.id,
                    "location_id": self.transit_location.id,
                    "location_dest_id": self.location_dest_id.id,
                    "move_lines": move_line,
                    "note":self.remark,
                    })
                self.delivery_check = True
                picking_out.action_confirm()
                action = {
                    'name': 'Transfer Delivery',
                    'type': 'ir.actions.act_window',
                    'res_model': 'stock.picking',
                    'res_id': picking_out.id, 'view_mode': 'form',
                    }
                return action
            else:
                raise ValidationError(_("Not Out Type in Warehouse"))
            
    def create_receipt(self):
        picking_id_out = self.env['stock.picking'].search([('b_c_urgent_delivery_id', '=', self.id),('picking_type_id.code','=','outgoing')])
        if picking_id_out.state != 'done':
            raise ValidationError(_("Please complete Delivery Pickings (Status: Done) before creating Receipt."))
        if self.to_warehouse:
            move_line = []
            company_id = self.env.company.id
            # INCOMING ------------
            if self.from_warehouse.inter_transfer_receive:
                for move in self.b_c_urgent_delivery_line:
                    qty_remain = move.qty - move.urgent_pick
                    move_line.append((0, 0, {
                        "product_id": move.product_id.id,
                        "name": move.product_id.name,
                        "product_uom_qty": move.qty,
                        "product_uom": move.product_uom.id,
                        "company_id": company_id,
                        "location_id": self.location_dest_id.id,
                        "location_dest_id": self.location_id.id,
                        "qty_remain":qty_remain,
                        "urgent_pick": move.urgent_pick,
                        "urgent_remain": move.urgent_pick,
                        "urgent_location_ids": move.urgent_location_ids,
                        }))

                picking_in = self.env["stock.picking"].create({
                    "picking_type_id": self.from_warehouse.inter_transfer_receive.id if self.from_warehouse.inter_transfer_receive else self.from_warehouse.in_type_id.id,
                    "b_c_urgent_delivery_id":self.id,
                    "location_id": self.location_dest_id.id,
                    "location_dest_id": self.location_id.id,
                    "move_lines": move_line
                    })
                picking_in.action_confirm()
                self.receipt_check = True
                if picking_in.b_c_urgent_delivery_id:
                    for move in picking_in.move_lines:
                        move.create_move_line_b_c_urgen()
                action = {
                    'name': 'Transfer Receipts',
                    'type': 'ir.actions.act_window',
                    'res_model': 'stock.picking',
                    'res_id': picking_in.id, 'view_mode': 'form',
                    }
                return action
            else:
                raise ValidationError(_("Not In Type in Warehouse"))

    def action_open_urgent_delivery_lines(self):
        self.ensure_one()
        return {
            'name': 'Booth and Consignment Urgent Delivery Transfer Lines',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'booth.consign.urgent.delivery.line',
            'domain': [('b_c_urgent_delivery_id', '=', self.id)],
            'context': {'default_b_c_urgent_delivery_id': self.id},
        }

class BoothConsignUrgentDeliveryLine(models.Model):
    _name = "booth.consign.urgent.delivery.line"
    _description = "Booth and Consignment Urgent Delivery Line Transfer"

    b_c_urgent_delivery_id = fields.Many2one('booth.consign.urgent.delivery', string = 'Booth Consign Urgent Delivery Transfer')
    ud_state = fields.Selection(related="b_c_urgent_delivery_id.state")
    ud_date = fields.Datetime(related="b_c_urgent_delivery_id.date")
    ud_name = fields.Char(related="b_c_urgent_delivery_id.name")
    ud_delivery_date = fields.Datetime(related="b_c_urgent_delivery_id.delivery_date")

    product_id = fields.Many2one("product.product", string = 'Product')
    qty = fields.Float("Demand", digits = 'Product Unit of Measure')
    urgent_pick = fields.Float(string='Urgent Pick')
    urgent_location_ids = fields.Many2many('stock.location', string='Urgent Location')
    sale_order_ids = fields.Many2many('sale.order',string = "Sale Order")
    product_uom = fields.Many2one("uom.uom", string = "UOM",)
    qty_remain = fields.Float(string='Remain Stock',compute="_compute_qty_remain",)
    source_location_id = fields.Many2one(related = "b_c_urgent_delivery_id.transit_location",store=True)
    qty_inventory_quantity = fields.Float("On Hand Quantity", compute="_compute_onhand", digits = 'Product Unit of Measure', readonly = True)
    qty_available_quantity = fields.Float("Available Quantity", compute="_compute_onhand", digits = 'Product Unit of Measure', readonly = True)
    
    @api.depends("qty", "urgent_pick")
    def _compute_qty_remain(self):
        for rec in self:
            rec.qty_remain = rec.qty - rec.urgent_pick

    @api.depends("source_location_id")
    def _compute_onhand(self):
        for rec in self:
            qty_inventory_quantity = 0
            qty_available_quantity = 0
            quant_id = rec.env['stock.quant'].search([('product_id','=', rec.product_id.id),('location_id','=',rec.source_location_id.id)])
            if quant_id:
                for quant in quant_id:
                    qty_inventory_quantity += quant.quantity
                    qty_available_quantity += quant.available_quantity
                rec.qty_inventory_quantity = qty_inventory_quantity
                rec.qty_available_quantity = qty_available_quantity
            else:
                rec.qty_inventory_quantity = 0
                rec.qty_available_quantity = 0


    


