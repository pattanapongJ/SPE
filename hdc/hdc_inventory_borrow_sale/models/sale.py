# -*- coding: utf-8 -*-


import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.tools.float_utils import float_repr
from odoo.tools.misc import format_date
from odoo.exceptions import Warning, ValidationError, UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    borrow_count = fields.Integer(string = 'Borrow Orders', compute = '_compute_borrow_ids')
    deduct_borrow_count = fields.Integer(string = 'Borrow Orders', compute = '_compute_borrow_ids')
    is_borrow = fields.Boolean(related='type_id.is_borrow')
    
    def action_confirm(self):
        addition = self.env["addition.operation.type"].search([("code", "=", "AO-02")], limit=1)
        picking_type = self.env["stock.picking.type"].search([("addition_operation_types", "=", addition.id)])
        picking = self.env["stock.picking"].search([("sale_borrow", "=", self.id),("picking_type_id", "in", picking_type.ids)])
        check_borrow_done = True
        for picking_id in picking:
            if picking_id.state not in ["cancel", "done"]:
                check_borrow_done = False
                break
        if check_borrow_done:
            res = super(SaleOrder, self).action_confirm()
            if self.borrow_count > 0:
                self.create_deduct_product_picking()
            return res
        else:
            return {
                "name": "Confirm ?",
                "type": "ir.actions.act_window",
                "res_model": "check.force.done",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_sale_order_id": self.id},
            }
        
    def get_lots_from_borrow_and_return(self, picking_borrows, picking_return_borrow):
        """ดึง lot ทั้งหมดจาก borrow_pick และ return_pick"""
        borrow_lots = []
        return_lots = []

        # ดึง lot จาก picking_borrows
        for borrow_pick in picking_borrows:
            for move in borrow_pick.move_ids_without_package:
                for line in move.move_line_ids:
                    if line.lot_id:
                        borrow_lots.append({
                            'lot_id': line.lot_id.id,
                            'product_id': line.product_id.id,
                            'qty_done': line.qty_done,
                            'location_id': line.location_id.id,
                            'location_dest_id': line.location_dest_id.id
                        })

        # ดึง lot จาก picking_return_borrow
        for return_pick in picking_return_borrow:
            for move in return_pick.move_ids_without_package:
                for line in move.move_line_ids:
                    if line.lot_id:
                        return_lots.append({
                            'lot_id': line.lot_id.id,
                            'product_id': line.product_id.id,
                            'qty_done': line.qty_done,
                            'location_id': line.location_id.id,
                            'location_dest_id': line.location_dest_id.id
                        })

        return borrow_lots, return_lots

    def get_different_lots(self, borrow_lots, return_lots):
        """หาความแตกต่างของ lot ระหว่าง borrow_lots และ return_lots"""
        # สร้าง dictionary สำหรับเก็บจำนวนคงเหลือของ borrow_lots
        borrow_lot_dict = {}
        for lot in borrow_lots:
            key = (lot['lot_id'], lot['product_id'])
            if key in borrow_lot_dict:
                borrow_lot_dict[key] += lot['qty_done']
            else:
                borrow_lot_dict[key] = lot['qty_done']

        # หักจำนวนคืนใน return_lots ออกจาก borrow_lot_dict
        for lot in return_lots:
            key = (lot['lot_id'], lot['product_id'])
            if key in borrow_lot_dict:
                borrow_lot_dict[key] -= lot['qty_done']
                if borrow_lot_dict[key] <= 0:
                    del borrow_lot_dict[key]  # ลบออกถ้าไม่มีเหลือ

        # สร้างรายการ lot ที่ยังคงเหลือหลังหักการคืนออกไป
        different_lots = [
            {'lot_id': key[0], 'product_id': key[1], 'remaining_qty': qty}
            for key, qty in borrow_lot_dict.items()
        ]

        return different_lots

    def create_stock_move_lines(self, picking_in, different_lots):
        """สร้าง stock move line สำหรับ picking_in ตาม lot ที่เหลือ"""
        for move in picking_in.move_lines:
            move_lines_to_create = []
            # หา lot ที่ตรงกับ product_id ของ move
            relevant_lots = [lot for lot in different_lots if lot['product_id'] == move.product_id.id]

            if relevant_lots:
                # ถ้ามี lot ให้สร้าง move line ตาม lot
                for lot_info in relevant_lots:
                    move_lines_to_create.append((0, 0, {
                        'product_id': move.product_id.id,
                        'lot_id': lot_info['lot_id'],
                        'product_uom_id': move.product_uom.id,
                        'qty_done': lot_info['remaining_qty'],
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'move_id': move.id,
                    }))
            else:
                # ถ้าไม่มี lot ให้สร้าง move line ตามจำนวนที่ต้องการ (demand)
                move_lines_to_create.append((0, 0, {
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'qty_done': move.product_uom_qty,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'move_id': move.id,
                }))
            
            # อัพเดต move_line_ids
            move.move_line_ids = move_lines_to_create

    def create_deduct_product_picking(self):
        picking_type = self.type_id.picking_type_deduct_borrow_id
        if not picking_type:
            return 
            # raise ValidationError(_("Not set operation type Deduct Borrow"))
        picking_type_borrow = self.type_id.picking_borrow_type_id
        if not picking_type_borrow:
            raise ValidationError(_("Not set operation type Borrow"))

        # หา picking ที่เป็นการยืม
        picking_borrows = self.env["stock.picking"].search([
            ("sale_borrow", "=", self.id),
            ("picking_type_id", "=", picking_type_borrow.id)
        ])

        if picking_borrows:
            # หา picking ที่เป็นการคืน
            picking_return_borrows = self.env["stock.picking"].search([
                ("return_picking_form_id", "in", picking_borrows.ids)
            ])
            # สร้าง dictionary เพื่อเก็บข้อมูลสินค้าและจำนวน
            product_qty_borrowed = {}
            product_qty_returned = {}
            

            # รวมจำนวนสินค้าที่ทำการยืม
            for picking in picking_borrows:
                for move_line in picking.move_line_ids:
                    product = move_line.product_id
                    qty = move_line.product_uom_id._compute_quantity(move_line.qty_done, product.uom_id)
                    if product in product_qty_borrowed:
                        product_qty_borrowed[product] += qty
                    else:
                        product_qty_borrowed[product] = qty

            # รวมจำนวนสินค้าที่ทำการคืน
            for picking in picking_return_borrows:
                for move_line in picking.move_line_ids:
                    product = move_line.product_id
                    qty = move_line.product_uom_id._compute_quantity(move_line.qty_done, product.uom_id)
                    if product in product_qty_returned:
                        product_qty_returned[product] += qty
                    else:
                        product_qty_returned[product] = qty

            # คำนวณจำนวนสินค้าที่เหลืออยู่
            remaining_products = {}
            for product, borrowed_qty in product_qty_borrowed.items():
                returned_qty = product_qty_returned.get(product, 0)
                remaining_qty = borrowed_qty - returned_qty
                if remaining_qty > 0:
                    remaining_products[product] = remaining_qty

            # วนลูปเพื่อตรวจสอบสินค้าที่ไม่ได้ถูกคืน
            move_lines = []
            for product, qty in remaining_products.items():
                product_uom = product.uom_id
                company_id = self.company_id.id

                move_lines.append((0, 0, {
                    "product_id": product.id,
                    "name": product.display_name,
                    "product_uom_qty": qty,
                    "product_uom": product_uom.id,
                    "company_id": company_id,
                    "location_id": picking_type.default_location_src_id.id,
                    "location_dest_id": picking_type.default_location_dest_id.id,
                }))

            # ถ้ามี move_line ให้สร้าง picking ใหม่
            if move_lines:
                picking_in = self.env["stock.picking"].create({
                    "picking_type_id": picking_type.id,
                    "origin": self.name,
                    "sale_borrow": self.id,
                    "is_deduct_borrow": True,
                    "partner_id": self.partner_id.id,
                    "location_id": picking_type.default_location_src_id.id,
                    "location_dest_id": picking_type.default_location_dest_id.id,
                    "move_lines": move_lines
                })
                # ยืนยัน picking ใหม่
                picking_in.action_confirm()
                picking_in.action_assign()
                # ปิดจบ picking แบบอัตโนมัติ
                borrow_lots, return_lots = self.get_lots_from_borrow_and_return(picking_borrows,picking_return_borrows)
                different_lots = self.get_different_lots(borrow_lots, return_lots)
                self.create_stock_move_lines(picking_in, different_lots)
                validate = picking_in.button_validate()
                if validate != True:
                    # Check if the validate result is asking for "Immediate Transfer"
                    context = {
                        'active_model': 'stock.picking', 'active_ids': [picking_in.ids], 'active_id': picking_in.id,
                        }
                    if validate.get('name') == "Immediate Transfer?":
                        immediate_transfer_wizard = self.env['stock.immediate.transfer'].with_context(context).create({
                            'pick_ids': validate.get('context').get('default_pick_ids'),
                            'immediate_transfer_line_ids': [(0, 0, {'to_immediate': True, 'picking_id': picking_in.id})]
                            })
                        immediate = immediate_transfer_wizard.with_context(button_validate_picking_ids=picking_in.id).process()
                
    # def action_cancel(self):
    #     addition = self.env["addition.operation.type"].search([("code", "=", "AO-02")], limit=1)
    #     for order in self:
    #         picking_type = self.env["stock.picking.type"].search([("addition_operation_types", "=", addition.id)])
    #         if order.borrow_count > 0:
    #             picking = self.env["stock.picking"].search([("sale_borrow", "=", self.id),("picking_type_id", "in", picking_type.ids)])
    #             for line in order.order_line:
    #                 move = self.env["stock.move"].search([("product_id", "=", line.product_id.id),("picking_id", "in", picking.ids),("state", "!=", "cancel")])
    #                 sum_qty = sum(move.mapped("product_uom_qty"))
    #                 if sum_qty > line.return_qty:
    #                     raise ValidationError(_("Please check the product quality from borrow requst."))
    #     res = super(SaleOrder, self).action_cancel()
    #     return res

    def _compute_borrow_ids(self):
        for order in self:
            pickings = self.env["stock.picking"].search([("sale_borrow", "=", order.id)])
            order.borrow_count = len(pickings.filtered(lambda p: not p.is_deduct_borrow))
            order.deduct_borrow_count = len(pickings.filtered(lambda p: p.is_deduct_borrow))


    def action_view_borrow(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        pickings = self.env["stock.picking"].search([("sale_borrow", "=", self.id),("is_deduct_borrow","=",False)])
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(self._context, default_partner_id = self.partner_id.id,
                                 default_picking_type_id = picking_id.picking_type_id.id, default_origin = self.name,
                                 default_group_id = picking_id.group_id.id)
        return action
    
    def action_view_deduct_borrow(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        pickings = self.env["stock.picking"].search([("sale_borrow", "=", self.id),("is_deduct_borrow","=",True)])
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(self._context, default_partner_id = self.partner_id.id,
                                 default_picking_type_id = picking_id.picking_type_id.id, default_origin = self.name,
                                 default_group_id = picking_id.group_id.id)
        return action

    def action_create_borrow(self):
        self.ensure_one()
        picking = self.env["stock.picking"]
        addition = self.env["addition.operation.type"].search([("code", "=", "AO-02")], limit=1)
        if addition:
            if self.type_id.is_borrow:
                picking_type = self.type_id.picking_borrow_type_id
            else:
                picking_type = self.env["stock.picking.type"].search([("addition_operation_types", "=", addition.id),('company_id','=',self.company_id.id),('warehouse_id','=',self.warehouse_id.id)], limit = 1)
            if picking_type:
                order_line_ids = []
                for line in self.order_line:
                    picking = self.env["stock.picking"].search([("sale_borrow", "=", self.id),("picking_type_id", "=", picking_type.id)])
                    move = self.env["stock.move"].search([("product_id", "=", line.product_id.id),("picking_id", "in", picking.ids),("state", "!=", "cancel")])
                    sum_qty = sum(move.mapped("product_uom_qty"))
                    product_uom_qty = line.product_uom_qty - sum_qty + line.return_qty
                    if product_uom_qty < 0:
                        product_uom_qty = 0
                    if line.product_id == self.default_product_global_discount:
                        continue
                    vals = (0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_uom_qty': product_uom_qty,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': picking_type.default_location_dest_id.id,
                        'product_uom': line.product_uom.id,
                        })
                    order_line_ids.append(vals)
                context = {
                            "default_requester_emp": self.user_id.id,
                            "default_picking_type_id": picking_type.id,
                            "default_origin": self.name,
                            "default_sale_borrow": self.id,
                            "default_move_ids_without_package": order_line_ids
                        }
                return {
                    "type": "ir.actions.act_window",
                    "name": _("Borrow"),
                    "res_model": "stock.picking",
                    "view_mode": "form",
                    "context": context,
                    }
            else:
                raise ValidationError(_("Not set operation type Borrow"))
        else:
            raise ValidationError(_("Not set addition type Borrow"))

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    return_qty = fields.Float('Return QTY', copy=False)
    borrow_qty = fields.Float('Borrow QTY', copy=False)

    def _get_outgoing_incoming_moves(self):
        
        outgoing_moves = self.env['stock.move']
        incoming_moves = self.env['stock.move']

        for move in self.move_ids.filtered(lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id):
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                    outgoing_moves |= move
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                incoming_moves |= move

        return outgoing_moves, incoming_moves

    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_delivered(self):
        res = super(SaleOrderLine, self)._compute_qty_delivered()
        # addition = self.env["addition.operation.type"].search([("code", "=", "AO-02")], limit = 1)
        # if addition:
        #     picking_type = self.env["stock.picking.type"].search([("addition_operation_types", "=", addition.id)],limit = 1)
        for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
            if line.qty_delivered_method == 'stock_move':
                qty = 0.0
                outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
                for move in outgoing_moves:
                    if move.state != 'done':
                        continue
                    qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')
                for move in incoming_moves:
                    if move.state != 'done':
                        continue
                    qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')
                picking = self.env["stock.picking"].search([("sale_borrow", "=", line.order_id.id)],limit=1)
                # if picking :
                    # picking = self.env["stock.picking"].search([("sale_borrow", "=", line.order_id.id),("picking_type_id", "=", picking_type.id)],limit=1)
                if picking:
                    total_delivered = line.borrow_qty - line.return_qty
                    if total_delivered >=0:
                        qty += total_delivered
                line.qty_delivered = qty
        return res

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order' or line.product_id.type == 'service':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    # def _action_launch_stock_rule(self, previous_product_uom_qty=False):
    #     """
    #     Launch procurement group run method with required/custom fields genrated by a
    #     sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
    #     depending on the sale order line product rule.
    #     """
    #     precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #     procurements = []
    #     for line in self:
    #         line = line.with_company(line.company_id)
    #         if line.state != 'sale' or not line.product_id.type in ('consu','product'):
    #             continue
    #         qty = line._get_qty_procurement(previous_product_uom_qty)
    #         if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
    #             continue

    #         group_id = line._get_procurement_group()
    #         if not group_id:
    #             group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
    #             line.order_id.procurement_group_id = group_id
    #         else:
    #             # In case the procurement group is already created and the order was
    #             # cancelled, we need to update certain values of the group.
    #             updated_vals = {}
    #             if group_id.partner_id != line.order_id.partner_shipping_id:
    #                 updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
    #             if group_id.move_type != line.order_id.picking_policy:
    #                 updated_vals.update({'move_type': line.order_id.picking_policy})
    #             if updated_vals:
    #                 group_id.write(updated_vals)

    #         values = line._prepare_procurement_values(group_id=group_id)
    #         addition = self.env["addition.operation.type"].search([("code", "=", "AO-02")], limit = 1)
    #         product_qty = line.product_uom_qty
    #         if addition:
    #             picking_type = self.env["stock.picking.type"].search([("addition_operation_types", "=", addition.id)])
    #             if picking_type:
    #                 picking = self.env["stock.picking"].search([("sale_borrow", "=", line.order_id.id),("picking_type_id", "in", picking_type.ids)])
    #                 move = self.env["stock.move"].search(
    #                     [("product_id", "=", line.product_id.id),
    #                      ("picking_id", "in", picking.ids), ("state", "!=", "cancel")])
    #                 sum_qty = sum(move.mapped("product_uom_qty"))
    #                 product_uom_qty = line.product_uom_qty - sum_qty + line.return_qty
    #                 if product_uom_qty < 0:
    #                     product_uom_qty = 0
    #                 product_qty = product_uom_qty
    #         else:
    #             product_qty = line.product_uom_qty - qty

    #         line_uom = line.product_uom
    #         quant_uom = line.product_id.uom_id
    #         product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
    #         procurements.append(self.env['procurement.group'].Procurement(
    #             line.product_id, product_qty, procurement_uom,
    #             line.order_id.partner_shipping_id.property_stock_customer,
    #             line.product_id.display_name, line.order_id.name, line.order_id.company_id, values))
    #     if procurements:
    #         self.env['procurement.group'].run(procurements)
    #     return True
    