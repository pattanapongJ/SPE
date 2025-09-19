# Copyright 2022 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _,api,fields, models
from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet
from itertools import groupby
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.exceptions import Warning

class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_retail_type_id = fields.Boolean(related='type_id.is_retail',string='Is Retail Sales Types')
    is_booth_type_id = fields.Boolean(related='type_id.is_booth',string='Is Booth Sales Types')
    internal_transfer_num = fields.Integer(string='Number of Internal Transfer',compute='_compute_internal_transfer_num',default=0)
    picking_booth_num = fields.Integer(string='Number of Picking Booth',compute='_compute_picking_booth_num',default=0)
    location_id = fields.Many2one('stock.location', string = 'Location')
    b_c_urgent_delivery_id = fields.Many2one('booth.consign.urgent.delivery', string = 'Booth Consign Urgent Delivery', tracking = True,copy=False)
    
    def _compute_internal_transfer_num(self):
        for line in self:
            internal_transfer_count = self.env['stock.picking'].search_count([('picking_type_id.code', '=','internal'),('addition_operation_types_code', '!=','AO-06'),('order_id', '=',line.id),('location_dest_id.is_booth','!=',True)]) 
            line.update({   
                 'internal_transfer_num': internal_transfer_count,
                })    
    def _compute_picking_booth_num(self):
        for line in self:
            picking_booth_count = self.env['stock.picking'].search_count([('picking_type_id.code', '=','internal'),('addition_operation_types_code', '!=','AO-06'),('order_id', '=',line.id),('location_dest_id.is_booth','=',True)]) 
            line.update({   
                 'picking_booth_num': picking_booth_count,
                })                
            
    def create_internal_transfer(self):
        context = {}
        picking_type = self.type_id.picking_type_id
        move_ids_without_package_data_list = []

        if self.type_id.is_retail:
            location_id = self.env["stock.location"].search([("is_retail", "=", True), ("company_id", "=", self.company_id.id),("warehouse_id","=",self.warehouse_id.id)], limit=1)
            if len(location_id) == 0:
                raise Warning(
                _("ไม่พบ Location Retail")
                )

        for rec in self.order_line:
            if rec.product_id.type == "product":
                location_out_id = rec.pick_location_id.id
                data_rec = (0,0,{
                "product_id":rec.product_id.id,
                "name":rec.product_id.display_name,
                "description_picking":rec.product_id.name,
                "location_id":location_out_id,
                "location_dest_id":location_id.id,
                "product_uom_qty":rec.product_uom_qty,
                "product_uom":rec.product_uom.id,
                "sale_order_line_b_c_r":rec.id,
                })
                move_ids_without_package_data_list.append(data_rec)

        context.update({
            'order_id' :self.id,
            'partner_id':self.partner_id.id,
            'team_id':self.team_id.id,
            'user_id':self.user_id.id,
            'picking_type_id' :picking_type.id,
            'location_id' :picking_type.default_location_src_id.id,
            'location_dest_id' :location_id.id,
            'move_ids_without_package': move_ids_without_package_data_list,
            })
        picking_internal = self.env["stock.picking"].create(context)
        picking_internal.location_dest_id = location_id.id
        num_sale_line = 0
        for rec in self.order_line:
            location_out_id = rec.pick_location_id.id
            num_pick_line = 0
            for move_line in picking_internal.move_ids_without_package:
                if isinstance(move_line.id, int):
                    if num_sale_line == num_pick_line:
                        move_line.location_id = location_out_id
                    num_pick_line +=1

            num_sale_line += 1

        return {
                'type': 'ir.actions.act_window',
                'name': 'Create Internal Transfer',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': picking_internal.id,
            }
    
    def action_view_internal_transfer_detail(self):   
        picking_ids = self.env['stock.picking'].search([('picking_type_id.code', '=','internal'),('order_id', '=',self.id),('location_dest_id.is_booth','!=',True)]) 
        if len(picking_ids) == 1:
            return {
                "name": _("รายละเอียด"),
                "view_mode": "form",
                "res_model": "stock.picking",
                "type": "ir.actions.act_window",
                'res_id': picking_ids.id,
                "flags": {"initial_mode": "view"},                
                }
        else:            
            return {
                "name": _("รายละเอียด"),
                "view_mode": "tree,form",
                "res_model": "stock.picking",
                "type": "ir.actions.act_window",
                "domain": [("id", "in", picking_ids.ids)],                
                }
        
    def create_picking_booth(self):
        context = {}
        picking_type = self.type_id.picking_type_id
        move_ids_without_package_data_list = []

        if self.type_id.is_booth:
                location_id = self.location_id
        list_item = {}
        if self.order_line:
            for rec in self.order_line:
                if rec.product_id.type != "service":
                    location_out_id = rec.pick_location_id.id
                    if location_out_id in list_item:
                        list_line = list_item.get(location_out_id)
                        data_list = list_line.get("move_ids_without_package")
                        data_rec = (0,0,{
                        "product_id":rec.product_id.id,
                        "name":rec.product_id.display_name,
                        "description_picking":rec.product_id.name,
                        "location_id":location_out_id,
                        "location_dest_id":location_id.id,
                        "product_uom_qty":rec.product_uom_qty,
                        "product_uom":rec.product_uom.id,
                        "sale_order_line_b_c_r":rec.id,
                        })
                        data_list.append(data_rec)
                    else:
                        data_rec = (0,0,{
                        "product_id":rec.product_id.id,
                        "name":rec.product_id.display_name,
                        "description_picking":rec.product_id.name,
                        "location_id":location_out_id,
                        "location_dest_id":location_id.id,
                        "product_uom_qty":rec.product_uom_qty,
                        "product_uom":rec.product_uom.id,
                        "sale_order_line_b_c_r":rec.id,
                        })
                        list_item[location_out_id] = {
                            'order_id' :self.id,
                            'partner_id':self.partner_id.id,
                            'team_id':self.team_id.id,
                            'user_id':self.user_id.id,
                            'picking_type_id' :picking_type.id,
                            'location_id' :location_out_id,
                            'location_dest_id' :location_id.id,
                            'move_ids_without_package': move_ids_without_package_data_list,
                            'move_ids_without_package': [data_rec]
                            }
        res_id = []
        for item in list_item:
            picking_booth = self.env["stock.picking"].create(list_item.get(item))
            picking_booth.location_id = item
            picking_booth.location_dest_id = location_id.id
            res_id.append(picking_booth.id)

        if len(res_id) == 1:
            return {
                "name": _("Create Picking Booth"),
                "view_mode": "form",
                "res_model": "stock.picking",
                "type": "ir.actions.act_window",
                'res_id': res_id[0],
                "flags": {"initial_mode": "view"},                
                }
        else:            
            return {
                "name": _("Create Picking Booth"),
                "view_mode": "tree,form",
                "res_model": "stock.picking",
                "type": "ir.actions.act_window",
                "domain": [("id", "in", res_id)],                
                }
    
    def action_view_picking_booth(self):   
        picking_ids = self.env['stock.picking'].search([('picking_type_id.code', '=','internal'),('order_id', '=',self.id),('location_dest_id.is_booth','=',True)]) 
        if len(picking_ids) == 1:
            return {
                "name": _("รายละเอียด"),
                "view_mode": "form",
                "res_model": "stock.picking",
                "type": "ir.actions.act_window",
                'res_id': picking_ids.id,
                "flags": {"initial_mode": "view"},                
                }
        else:            
            return {
                "name": _("รายละเอียด"),
                "view_mode": "tree,form",
                "res_model": "stock.picking",
                "type": "ir.actions.act_window",
                "domain": [("id", "in", picking_ids.ids)],                
                }
        
    def below_cost_warning_wizard_booth_retail(self, list_warning_below_cost=[]):

        messages = []

        for list in list_warning_below_cost:

            line_message = f"{list['product']}, price: {list['price']}, cost: {list['cost']}"
            messages.append(line_message)

        message = "Your order has found selling price below cost. \n" + "\n".join(
            messages
        )

        return {
            "name": _("Below Cost Warning Sale Order"),
            "type": "ir.actions.act_window",
            "res_model": "below.cost.warning.wizard.booth",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_sale_order_id": self.id,
                "default_message": message,
            },
        }
    
    def action_sale_ok2(self):
        if self.type_id.pass_delivery is False:
            if not (self.type_id.is_oversea or self.type_id.is_borrow or self.type_id.is_online):
                if not (self.type_id.inter_company_transactions or self.type_id.is_retail):
                    if self.delivery_trl:
                        if not self.delivery_trl_description:
                            raise ValidationError(_("กรุณาระบุรายละเอียดของ สายส่ง TRL"))
                    elif self.delivery_company:
                        if not self.delivery_company_description:
                            raise ValidationError(_("กรุณาระบุรายละเอียดของ Mode of Delivery"))
                    else:
                        raise ValidationError(_("กรุณาระบุสายส่ง TRL หรือ Mode of Delivery"))

        
        if self.type_id.is_retail or self.type_id.is_booth:
            # Check Price Below Cost -------------------
            list_warning_below_cost = []

            for line in self.order_line:

                in_pricelist = self.env["product.pricelist.item"].search(
                                [
                                    ("pricelist_id", "=", self.pricelist_id.id),
                                    ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                                ], limit=1
                            )
                
                if line.product_id.product_tmpl_id.type != "service":

                    fixed_price = line.price_unit
                    cost_price = in_pricelist.pricelist_cost_price or line.product_id.product_tmpl_id.standard_price

                    if cost_price > fixed_price:
                            
                        if in_pricelist:
                            if not self.pricelist_id.approve_below_cost:
                                list_warning_below_cost.append({'product':line.product_id.name, 'price': fixed_price, 'cost': cost_price})
                        else:
                            if line.product_id.product_tmpl_id.below_cost or self.type_id.below_cost:
                                list_warning_below_cost.append({'product':line.product_id.name, 'price': fixed_price, 'cost': cost_price})

            if list_warning_below_cost:
                if not self.is_confirm_below_cost:
                    return self.below_cost_warning_wizard_booth_retail(list_warning_below_cost)

            # ------------------------------------------

            if self.type_id.is_booth:
                location_id = self.location_id
            if self.type_id.is_retail:
                location_id = self.env["stock.location"].search([("is_retail", "=", True), ("company_id", "=", self.company_id.id),("warehouse_id","=",self.warehouse_id.id)], limit=1)
                if len(location_id) == 0:
                    raise Warning(
                    _("ไม่พบ Location Retail ของ Warehouse %s",self.warehouse_id.name)
                    )
            check_product_qty = True
            for rec in self.order_line:
                if rec.product_id.type == "product":
                    product_location = self.env['stock.quant'].search([('product_id','=', rec.product_id.id),('location_id','=',location_id.id)])
                    if product_location:
                        if rec.product_uom_qty > product_location.available_quantity:
                            check_product_qty = False
                    else:
                        check_product_qty = False

            if check_product_qty == True:
                res = super(SaleOrder, self).action_sale_ok2()

                if self.picking_ids:
                    for pick in self.picking_ids:
                        if pick.state in ['waiting','confirmed','draft','assigned']:
                            for line in pick.move_ids_without_package:
                                line.location_id = location_id
                                line.state = 'draft'
                            pick.state = 'draft'
                            pick.location_id = location_id
                            pick.action_confirm()
                            pick.action_assign()
        
                            for line in pick.move_ids_without_package:
                                line.qty_counted = line.product_uom_qty
                            pick.action_confirm_warehouse()
                            for line in pick.move_ids_without_package:
                                for move_line in line.move_line_ids:
                                    move_line.qty_done = move_line.product_uom_qty
                            pick.button_validate()
                return res
            else:
                raise Warning(
                    _("กรุณาตรวจสอบ stock สินค้าในพื้นที่ดังกล่าวอีกครั้ง หรือโอนย้ายสินค้าให้เพียงพอต่อการใช้งาน")
                    )
        else:
            return super(SaleOrder, self).action_sale_ok2()
        
    def action_create_booth_consign_urgent_delivery(self):
        self.ensure_one()

        if self.b_c_urgent_delivery_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "booth.consign.urgent.delivery",
                "view_mode": "form",
                "res_id": self.b_c_urgent_delivery_id.id,
                "target": "current",
            }
        
        if not self.warehouse_id:
            raise UserError(_("Cannot create Booth &amp; Consignment Urgent Delivery: Warehouse is not set on this Sale Order."))

        if not self.location_id:
            raise UserError(_("Cannot create Booth &amp; Consignment Urgent Delivery: Booth &amp; Consignment Location is not set on this Sale Order."))

        b_c_urgent_delivery_id = self.env["booth.consign.urgent.delivery"].create({
            "state": "in_progress",
            "sale_order_ids": [(4, self.id)],
            "from_warehouse": self.warehouse_id.id,
            "location_id": self.warehouse_id.lot_stock_id.id,
            "location_dest_id": self.warehouse_id.transit_location.id,
        })

        for line in self.order_line.filtered(lambda l: l.product_id and l.product_id.type == 'product'):
            self.env["booth.consign.urgent.delivery.line"].create({
                "b_c_urgent_delivery_id": b_c_urgent_delivery_id.id,
                "product_id": line.product_id.id,
                "product_uom": line.product_uom.id,
                "qty": line.product_uom_qty,
                "urgent_pick": line.product_uom_qty,
                "urgent_location_ids": [(4, self.location_id.id)],
                "sale_order_ids": [(4, self.id)],
            })

        self.b_c_urgent_delivery_id = b_c_urgent_delivery_id.id

        return {
            "type": "ir.actions.act_window",
            "res_model": "booth.consign.urgent.delivery",
            "view_mode": "form",
            "res_id": b_c_urgent_delivery_id.id,
            "target": "current",
        }
    
    def action_view_booth_consign_urgent_delivery(self):
        self.ensure_one()
        if not self.b_c_urgent_delivery_id:
            return

        return {
            "type": "ir.actions.act_window",
            "name": "Booth Consign Urgent Delivery",
            "res_model": "booth.consign.urgent.delivery",
            "view_mode": "form",
            "res_id": self.b_c_urgent_delivery_id.id,
            "target": "current",
        }
