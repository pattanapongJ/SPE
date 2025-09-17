from email.policy import default
import json
import time
from ast import literal_eval
from collections import defaultdict
from datetime import date
from itertools import groupby
from operator import attrgetter, itemgetter
from collections import defaultdict
from datetime import datetime

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, format_date, OrderedSet


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    operation_types = fields.Char(related='picking_type_id.addition_operation_types.addition_Operation_type')
    approve_inter = fields.Many2one('res.users', string = "Approved by")
    from_warehouse = fields.Many2one(related='picking_type_id.warehouse_id', string="To Warehouse")
    to_warehouse = fields.Many2one("stock.warehouse", string = "From Warehouse")
    transit_location = fields.Many2one("stock.location", string="Transit Location")
    approve_date = fields.Datetime(string = "Delivery Date")
    addition_operation_types = fields.Many2one(related = 'picking_type_id.addition_operation_types')
    # is_delivery_done = fields.Boolean(compute = '_check_is_delivery_done')
    addition_operation_types_code = fields.Char(related='addition_operation_types.code', store=True)
    inter_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("approve", "Waiting for Approve"),
            ("delivery", "Waiting for Delivery"),
            ("waiting_cancel", "Waiting For Cancel"),
            ("done", "Done"),
            ("ship", "Shipped"),
            ("cancel", "Cancelled"),
        ], string="Status", default="draft", index=True, store=True, copy=False
    )

    inter_transfer_base_id = fields.Many2one("stock.picking", string = "Inter Transfer Base")
    check_inter_transfer_base_id = fields.Boolean(compute='_compute_check_inter_transfer_base_id')
    def _compute_check_inter_transfer_base_id(self):
        for record in self:
            if record.inter_transfer_base_id:
                record.check_inter_transfer_base_id = True
            else:
                record.check_inter_transfer_base_id = False

    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    return_picking_form_id = fields.Many2one('stock.picking',string = 'Return Orders')
    return_count = fields.Integer(string = 'Return Orders', compute = '_compute_picking_ids')
    inter_state_name= fields.Char(string = 'Delivery Status', compute = '_compute_inter_state_name')

    check_receipt = fields.Boolean(compute='_compute_check_receipt')
    check_origin_inter = fields.Boolean(compute='_check_origin_inter')

    show_force_done = fields.Boolean(
        string="Show Force Done", 
        compute="_compute_show_force_done"
    )

    @api.depends('origin','state')
    def _compute_show_force_done(self):
        for record in self:
            deliveries = self.env['stock.picking'].search([
                ('origin', '=', record.name),
                ('picking_type_id.code', '=', 'outgoing')
            ])
            receipts = self.env['stock.picking'].search([
                ('origin', '=', record.name),
                ('picking_type_id.code', '=', 'incoming')
            ])

            all_not_done = all(delivery.state != 'done' for delivery in deliveries) and all(receipt.state != 'done' for receipt in receipts)
            delivery_done_receipt_ready = all(delivery.state == 'done' for delivery in deliveries) and all(receipt.state == 'assigend' for receipt in receipts)
            all_done = all(delivery.state == 'done' for delivery in deliveries) and all(receipt.state == 'done' for receipt in receipts)
            record.show_force_done = (all_not_done or delivery_done_receipt_ready) and not all_done

    @api.depends('picking_type_code')
    def _compute_check_receipt(self):
        for record in self:
            if record.picking_type_code == 'incoming':
                if record.picking_type_id.return_picking_type_id.code == 'outgoing':
                    record.check_receipt = True
                else:
                    record.check_receipt = False
            else:
                record.check_receipt = False
            
    @api.depends('write_date')
    def _compute_inter_state_name(self):
        for inter in self:
            if inter.inter_state == 'draft':
                inter.inter_state_name = "Draft"
            elif inter.inter_state == 'approve':
                inter.inter_state_name = "Waiting for Approve"
                inter.state = "assigned"
            elif inter.inter_state == 'delivery':
                inter.inter_state_name = "Waiting for Delivery"
                inter.state = "assigned"
            elif inter.inter_state == 'done':
                inter.inter_state_name = "Done"
                inter.state = "done"
            elif inter.inter_state == 'ship':
                inter.inter_state_name = "Shipped"
                inter.state = "done"
            elif inter.inter_state == 'waiting_cancel':
                inter.inter_state_name = "Waiting For Cancel"
                inter.state = "waiting_cancel"
            elif inter.inter_state == 'cancel':
                inter.inter_state_name = "Cancelled"
                inter.state = "cancel"

    @api.onchange('to_warehouse')
    def _onchange_to_warehouse(self):
        self.transit_location = self.to_warehouse.lot_stock_id.id

    def cancel_inter(self):
        picking_ids = self.env['stock.picking'].search([('origin', '=', self.name)])
        picking_in = self.env['stock.picking'].search_count([('origin', '=', self.name),('state', '=', 'done'),
                                                       ('picking_type_code', '=', 'incoming')])
        picking_out = self.env['stock.picking'].search_count(
            [('origin', '=', self.name),('state', '=', 'done'), ('picking_type_code', '=', 'outgoing')])

        if picking_ids:
            if picking_in != picking_out:
                language = self.env.context.get('lang')
                if language == 'th_TH':
                    raise ValidationError(_("ไม่สามารถยกเลิกได้เนื่องจากปลายทางมีการจัดส่งสินค้าแล้ว."))
                else:
                    raise ValidationError(_("Cancellation cannot be made because the product has already been shipped to the destination."))
            else:
                return {
                    "name": _("Reason for the cancellation"),
                    "view_type": "form", "view_mode": "form",
                    "res_model": "stock.picking.cancel",
                    "views": [(False, "form")],
                    "type": "ir.actions.act_window",
                    "context": {}, "target": "new",
                    }
        else:
            return {
                    "name": _("Reason for the cancellation"),
                    "view_type": "form",
                    "view_mode": "form",
                    "res_model": "stock.picking.cancel",
                    "views": [(False, "form")],
                    "type": "ir.actions.act_window",
                    "context": {},
                    "target": "new",
                }

        # self.is_locked = True
        # self.state = "cancel"
        # self.inter_state = "cancel"
        
    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        self.write({'state': 'cancel', 'inter_state': 'cancel'})
        return res

    def force_done_inter(self):
        for rec in self:
            rec.inter_state = "done"

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for inter in self:
            if inter.batch_id:
                continue
                
            if inter.state == "done":
                inter_pick_ids = self.env['stock.picking'].search([('name', '=', inter.origin)], limit=1)
                picking_in_type_id = self.env['stock.picking'].search([('origin', '=', inter_pick_ids.name), ('state', 'not in', ('done', 'cancel')), (
                'picking_type_id', '=', inter_pick_ids.from_warehouse.inter_transfer_receive.id)])

                picking_out_type_id = self.env['stock.picking'].search(
                    [('origin', '=', inter_pick_ids.name), ('state', '=', 'done'),
                    ('picking_type_id', '=', inter_pick_ids.to_warehouse.inter_transfer_delivery.id)])
                
                if picking_in_type_id:
                    inter.inter_state = 'done'
                    for pick in picking_in_type_id:
                        pick.action_confirm()
                        pick.action_assign()

                if picking_out_type_id:
                    inter.inter_state = 'done'
                    for move in picking_in_type_id.move_ids_without_package:
                        picking_out_move = picking_out_type_id.move_lines.filtered(lambda m: m.product_id == move.product_id and m.product_id.tracking != 'none')
                        if picking_out_move:
                            for line in picking_out_move.move_line_ids:
                                self.env['stock.move.line'].create({
                                    'move_id': move.id,
                                    'product_id': move.product_id.id,
                                    'product_uom_id': move.product_uom.id,
                                    'qty_done': line.qty_done,
                                    'location_id': move.location_id.id,
                                    'location_dest_id': move.location_dest_id.id,
                                    'lot_name': line.lot_id.name,
                                    'package_id': line.package_id.id,
                                    'owner_id': line.owner_id.id,
                                })
                    for pick in picking_out_type_id:
                        pick.inter_state = 'ship'

                if not picking_in_type_id and not picking_out_type_id:
                    if inter.picking_type_id.code == 'outgoing':
                        inter.inter_state = 'ship'
                    else:
                        inter.inter_state = 'done'
                if not picking_in_type_id and picking_out_type_id:
                    inter_pick_ids.inter_state = 'done'
                    inter_pick_ids.state = 'done'

                for picking in inter.sale_id.picking_ids.filtered(lambda m: m.state in ('waiting_cancel')):
                    if picking.state_before_cancel == 'done':
                        for line in picking.move_lines:
                            check_done = 0
                            for move in line.move_dest_ids.filtered(lambda m: m.state in ('done')):
                                check_done += move.product_uom_qty
                            if line.product_uom_qty != check_done:
                                return res
                            # picking.sale_id.state = 'cancel'
                            # picking.state = 'cancel'
                            # picking.inter_state = 'cancel'
                        return res
                if inter.picking_type_id.code == 'outgoing':
                    inter.delivery_out_done_to_in_done()
                                                          
        return res
    
    def delivery_out_done_to_in_done(self):
        for inter in self:
            if inter.picking_type_id.code == 'outgoing':
                picking_ids_in = False
                if inter.origin:
                    picking_ids_in = self.env['stock.picking'].search([('origin', '=', inter.origin),('state', 'not in', ['done','cancel']),('picking_type_id.code','=','incoming')])
                if picking_ids_in:
                    reference = picking_ids_in.name
                    for line in inter.move_ids_without_package:
                        move_in = self.env['stock.move'].search([('product_id',"=",line.product_id.id),('reference','=',reference)])
                        if move_in:
                            new_urgent_remain = move_in.urgent_remain
                            if move_in.urgent_remain == move_in.urgent_pick:
                                new_urgent_remain = move_in.urgent_pick - line.quantity_done
                                if new_urgent_remain < 0:
                                    new_urgent_remain = 0
                            else:
                                new_urgent_remain = move_in.urgent_remain - line.quantity_done
                                if new_urgent_remain < 0:
                                    new_urgent_remain = 0
                            new_delivery_done_out = move_in.delivery_done_out + line.quantity_done
                            move_in.update({'delivery_done_out': new_delivery_done_out})
                            move_in.update({'urgent_remain': new_urgent_remain})

    def open_delivery(self):
        self.ensure_one()
        tree_view = self.env.ref("stock.vpicktree", raise_if_not_found = False)
        form_view = self.env.ref("stock.view_picking_form", raise_if_not_found = False)
        action = {
            "type": "ir.actions.act_window",
            "name": "Transfer Delivery & Receipts",
            "res_model": "stock.picking",
            "view_mode": "tree, form",
            "domain": [("origin", "=", self.name)],
            }
        if tree_view and form_view:
            action["views"] = [(tree_view.id, "tree"), (form_view.id, "form")]
        return action

    def open_return(self):
        self.ensure_one()
        return_id = []
        picking_ids = self.env['stock.picking'].search([('origin', '=', self.name)])
        for pick in picking_ids:
            return_ids = self.env['stock.picking'].search([('return_picking_form_id', '=', pick.id)])
            if return_ids:
                return_id = return_ids.ids
        tree_view = self.env.ref("stock.vpicktree", raise_if_not_found = False)
        form_view = self.env.ref("stock.view_picking_form", raise_if_not_found = False)
        action = {
            "type": "ir.actions.act_window",
            "name": "Return Orders",
            "res_model": "stock.picking",
            "view_mode": "tree, form",
            "domain": [("id", "in", return_id)],
            }
        if tree_view and form_view:
            action["views"] = [(tree_view.id, "tree"), (form_view.id, "form")]
        return action

    @api.depends('state', 'move_lines')
    def _compute_picking_ids(self):
        for order in self:
            picking_ids = self.env['stock.picking'].search([('origin', '=', order.name)])
            order.delivery_count = len(picking_ids)
            order.return_count = 0
            for pick in picking_ids:
                return_ids = self.env['stock.picking'].search([('return_picking_form_id', '=', pick.id)])
                order.return_count += len(return_ids)

            if order.move_lines:
                count = 0
                for move in order.move_lines:
                    if (move.return_done + move.receipt_done) != move.product_uom_qty or move.product_uom_qty == 0:
                        count = 1
                        break

                if count == 0:
                    order.inter_state = "done"

    def to_approve(self):
        if self.move_lines:
            self.is_locked = True
            self.state = "done"
            self.inter_state = "approve"

    def approve(self):
        if self.to_warehouse:
            # OUTGOING ------------
            move_line = []
            if self.to_warehouse.inter_transfer_delivery :
            # if self.to_warehouse.out_type_id:
                for move in self.move_lines:
                    move_line.append((0, 0, {
                        "product_id": move.product_id.id,
                        "name": move.name,
                        "product_uom_qty": move.product_uom_qty,
                        "product_uom": move.product_uom.id,
                        "company_id": move.company_id.id,
                        "location_id": self.transit_location.id,
                        "location_dest_id": self.location_dest_id.id,
                        "urgent_pick": move.urgent_pick_inter,
                        "urgent_remain": move.urgent_pick_inter,
                        "remark": move.remark,
                        "description_picking":move.description_picking
                        }))

                picking_out = self.env["stock.picking"].create({
                    "picking_type_id": self.to_warehouse.inter_transfer_delivery.id if self.to_warehouse.inter_transfer_delivery else  self.to_warehouse.out_type_id.id,
                    "origin": self.name,
                    "partner_id": self.partner_id.id,
                    "location_id": self.transit_location.id,
                    "location_dest_id": self.location_dest_id.id,
                    "move_lines": move_line,
                    "inter_type_id": self.inter_type_id.id,
                    "inter_transfer_base_id": self.id,
                    "remark": self.remark,
                    "note": self.note,
                    })
                picking_out.action_confirm()
            else:
                raise ValidationError(_("Not Out Type in Warehouse"))

            move_line = []
            # INCOMING ------------
            if self.from_warehouse.in_type_id:
                for move in self.move_lines:
                    move_line.append((0, 0, {
                        "product_id": move.product_id.id,
                        "name": move.name,
                        "product_uom_qty": move.product_uom_qty,
                        "product_uom": move.product_uom.id,
                        "company_id": move.company_id.id,
                        "location_id": self.location_dest_id.id,
                        "location_dest_id": self.location_id.id,
                        "urgent_pick": move.urgent_pick_inter,
                        "urgent_remain": move.urgent_pick_inter,
                        "remark": move.remark,
                        "description_picking":move.description_picking
                        }))

                picking_in = self.env["stock.picking"].create({
                    "picking_type_id": self.from_warehouse.inter_transfer_receive.id if self.from_warehouse.inter_transfer_receive else self.from_warehouse.in_type_id.id,
                    "origin": self.name,
                    "partner_id": self.partner_id.id,
                    "location_id": self.location_dest_id.id,
                    "location_dest_id": self.location_id.id,
                    "move_lines": move_line,
                    "inter_type_id": self.inter_type_id.id,
                    "inter_transfer_base_id": self.id,
                    "remark": self.remark,
                    "note": self.note,
                    })
                picking_in.action_confirm()
            else:
                raise ValidationError(_("Not In Type in Warehouse"))

            self.inter_state = "delivery"
            self.approve_inter = self.env.user.id

    def revise(self):
        self.is_locked = False
        self.state = "draft"
        self.inter_state = "draft"
    
    @api.depends('origin')
    def _check_origin_inter(self):
        for record in self:
            if record.picking_type_code == 'incoming':
                picking_ids_in = self.env['stock.picking'].search([('name', '=', record.origin)])

                if picking_ids_in.addition_operation_types_code == 'AO-06':
                    record.check_origin_inter = True
                else:
                    record.check_origin_inter = False
            else:
                record.check_origin_inter = False

    @api.model
    def create(self, vals):
        location_id_list = []
        location_dest_id_list = []
        moves = vals.get('move_lines', []) + vals.get('move_ids_without_package', [])
        if moves and ((vals.get('location_id') and vals.get('location_dest_id')) or vals.get('partner_id')):
            for move in moves:
                location_id_list.append(move[2].get('location_id'))
                location_dest_id_list.append(move[2].get('location_dest_id'))
        res = super(StockPicking, self).create(vals)
        index = 0
        for move_line in res.move_ids_without_package:
            if isinstance(move_line.id, int):
                move_line.location_id = location_id_list[index]
                move_line.location_dest_id = location_dest_id_list[index]
                index += 1
        return res
    
    def update_description_picking_product_name(self):
        for rec in self:
            for move in rec.move_lines:
                move.description_picking = move.product_id.name

class StockMove(models.Model):
    _inherit = "stock.move"
    
    return_value = fields.Float(string="Return", readonly=True)
    scrap_value = fields.Float(string="Scrap", readonly=True)
    scrap_return = fields.Float(string="Scrap", readonly=True)
    receipt_done = fields.Float(string = 'Receipts Done', compute = '_check_delivery_done')
    return_done = fields.Float(string = 'Return Done', compute = '_check_delivery_done')
    delivery_done = fields.Float(string='Delivery Done', compute='_check_delivery_done')
    check_receipt = fields.Boolean(related='picking_id.check_receipt')
    delivery_done_out = fields.Float(string='Delivery Done (Out)',copy=False,default=0)
    urgent_pick = fields.Float(string='Urgent Pick')
    urgent_pick_inter = fields.Float(string='Urgent Pick')
    urgent_remain = fields.Float(string='Urgent Remain')
    urgent_remain_done = fields.Float(string='Urgent Remain',compute='_compute_urgent_remain_done')
    urgent_location_ids = fields.Many2many('stock.location', string='Urgen Location')

    free_qty = fields.Float(string='Onhand',digits=(16, 2),compute='_compute_free_qty')
    
    def get_stock_onhand_company(self, company_id,location_id):
        inter_location = self.env['inter.transfer.onhand.location'].search([
            ('company_id', '=', company_id.id),
            ('location_id', '=', location_id.id)
        ], limit=1)

        if not inter_location or not inter_location.inter_onhand_location_ids:
            return 0

        location_ids = inter_location.inter_onhand_location_ids.ids

        quants = self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id', 'in', location_ids),
            ('location_id.usage', '=', 'internal'),
            ('company_id', '=', company_id.id)
        ])

        total_available_quantity = sum(q.available_quantity for q in quants)
        return total_available_quantity

    @api.onchange('product_id','location_id')
    def _onchange_product_id_location(self):
        if self.picking_id.addition_operation_types_code == 'AO-06':
            if self.product_id and self.location_id:
                company_id = self.company_id
                location_id = self.location_id
                free_qty = self.get_stock_onhand_company(company_id,location_id)
                self.free_qty = free_qty
            else:
                self.free_qty = 0
        else:
            self.free_qty = 0
    
    def _compute_free_qty(self):
        for rec in self:
            if rec.picking_id.addition_operation_types_code == 'AO-06':
                if rec.product_id and rec.location_id:
                    company_id = rec.company_id
                    location_id = rec.location_id
                    free_qty = rec.get_stock_onhand_company(company_id,location_id)
                    rec.free_qty = free_qty
                else:
                    rec.free_qty = 0
            else:
                rec.free_qty = 0

    @api.model
    def _default_location_id(self):
        default_addition_operation_types_code = self._context.get('default_addition_operation_types_code')
        default_location_id = self._context.get('location')
        default_transit_location = self._context.get('transit_location')

        if default_addition_operation_types_code == 'AO-06':
            return default_transit_location
        return default_location_id
    
    @api.model
    def _default_location_dest_id(self):
        default_addition_operation_types_code = self._context.get('default_addition_operation_types_code')
        default_location_id = self._context.get('location')
        default_location_dest_id = self._context.get('location_dest')
        
        if default_addition_operation_types_code == 'AO-06':
            return default_location_id
        return default_location_dest_id

    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        auto_join=True, index=True, required=True,
        check_company=True,default=lambda self: self._default_location_id(),
        help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations.")
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        auto_join=True, index=True, required=True,
        check_company=True,default=lambda self: self._default_location_dest_id(),
        help="Location where the system will stock the finished products.")
    
    # def action_explode(self):
    #     # ข้ามการแปลงของจากตัว FG เป็น component ที่ bom type = kit 
    #     for move in self:
    #         inter_pick_id = self.env['stock.picking'].search([('name', '=', move.picking_id.origin)], limit=1)
    #         if inter_pick_id.addition_operation_types_code == 'AO-06':
    #             return move
    #     return super().action_explode()

    def _check_delivery_done(self):
        for rec in self:
            return_dict = {}
            delivery_dict = {}
            receipt_dict = {}

            picking_ids = self.env['stock.picking'].search([('origin', '=', rec.picking_id.name), ('state', '=', 'done'),
                                                            ('picking_type_id', '=', rec.picking_id.from_warehouse.inter_transfer_receive.id)])
            picking_ids_2 = self.env['stock.picking'].search(
                [('origin', '=', rec.picking_id.name), ('state', '=', 'done'),
                 ('picking_type_id', '=', rec.picking_id.to_warehouse.inter_transfer_delivery.id)])

            for pick in picking_ids:
                for move in pick.move_lines:
                    if receipt_dict.get(move.product_id.id):
                        receipt_dict[move.product_id.id] += move.quantity_done
                    else:
                        receipt_dict[move.product_id.id] = move.quantity_done

                picking_ids_3 = self.env['stock.picking'].search([('return_picking_form_id', '=', pick.id), ('state', '=', 'done')])
                
                for pick3 in picking_ids_3:
                    for move3 in pick3.move_lines:
                        if return_dict.get(move3.product_id.id):
                            return_dict[move3.product_id.id] += move3.quantity_done
                        else:
                            return_dict[move3.product_id.id] = move3.quantity_done

            for pick in picking_ids_2:
                for move in pick.move_lines:
                    if delivery_dict.get(move.product_id.id):
                        delivery_dict[move.product_id.id] += move.quantity_done
                    else:
                        delivery_dict[move.product_id.id] = move.quantity_done

            #borrow
            if rec.picking_type_id.addition_operation_types.code == "AO-02":
                picking_ids_3 = self.env['stock.picking'].search([('return_picking_form_id', '=', rec.picking_id.id), ('state', '=', 'done')])
                for pick3 in picking_ids_3:
                    for move3 in pick3.move_lines:
                        if return_dict.get(move3.product_id.id):
                            return_dict[move3.product_id.id] += move3.quantity_done
                        else:
                            return_dict[move3.product_id.id] = move3.quantity_done

            rec.return_done = return_dict.get(rec.product_id.id) or 0
            rec.delivery_done = delivery_dict.get(rec.product_id.id) or 0
            rec.receipt_done = receipt_dict.get(rec.product_id.id) or 0

    def _action_assign(self):
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `product_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """
        StockMove = self.env['stock.move']
        assigned_moves_ids = OrderedSet()
        partially_available_moves_ids = OrderedSet()
        # Read the `reserved_availability` field of the moves out of the loop to prevent unwanted
        # cache invalidation when actually reserving the move.
        reserved_availability = {move: move.reserved_availability for move in self}
        roundings = {move: move.product_id.uom_id.rounding for move in self}
        move_line_vals_list = []
        for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            rounding = roundings[move]
            missing_reserved_uom_quantity = move.product_uom_qty - reserved_availability[move]
            missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity, move.product_id.uom_id, rounding_method='HALF-UP')

            if move._should_bypass_reservation():
                # create the move line(s) but do not impact quants
                if move.product_id.tracking == 'serial' and (move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                    for i in range(0, int(missing_reserved_quantity)):
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=1))
                else:
                    to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                            ml.location_id == move.location_id and
                                                            ml.location_dest_id == move.location_dest_id and
                                                            ml.picking_id == move.picking_id and
                                                            not ml.lot_id and
                                                            not ml.package_id and
                                                            not ml.owner_id)
                    if to_update:
                        to_update[0].product_uom_qty += missing_reserved_uom_quantity
                    else:
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=missing_reserved_quantity))
                        
                assigned_moves_ids.add(move.id)
            else:
                if float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                    assigned_moves_ids.add(move.id)
                elif not move.move_orig_ids:
                    if move.procure_method == 'make_to_order':
                        continue
                    # If we don't need any quantity, consider the move assigned.
                    need = missing_reserved_quantity
                    if float_is_zero(need, precision_rounding=rounding):
                        assigned_moves_ids.add(move.id)
                        continue
                    # Reserve new quants and create move lines accordingly.
                    forced_package_id = move.package_level_id.package_id or None
                    available_quantity = move._get_available_quantity(move.location_id, package_id=forced_package_id)
                    if available_quantity <= 0:
                        continue
                    taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id, package_id=forced_package_id, strict=False)
                    if float_is_zero(taken_quantity, precision_rounding=rounding):
                        continue
                    if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
                        assigned_moves_ids.add(move.id)
                    else:
                        partially_available_moves_ids.add(move.id)
                else:
                    # Check what our parents brought and what our siblings took in order to
                    # determine what we can distribute.
                    # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                    # the reserved quantity on the quants, convert it here in
                    # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                    # move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
                    move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
                    keys_in_groupby = ['location_dest_id', 'lot_id', 'result_package_id', 'owner_id']
                    def _keys_in_sorted(ml):
                        return (ml.location_dest_id.id, ml.lot_id.id, ml.result_package_id.id, ml.owner_id.id)

                    grouped_move_lines_in = {}
                    for k, g in groupby(sorted(move_lines_in, key=_keys_in_sorted), key=itemgetter(*keys_in_groupby)):
                        qty_done = 0
                        for ml in g:
                            qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                        grouped_move_lines_in[k] = qty_done

                    move_lines_out_done = (move.move_orig_ids.mapped('move_dest_ids') - move)\
                        .filtered(lambda m: m.state in ['done'])\
                        .mapped('move_line_ids')
                    # As we defer the write on the stock.move's state at the end of the loop, there
                    # could be moves to consider in what our siblings already took.
                    moves_out_siblings = move.move_orig_ids.mapped('move_dest_ids') - move
                    moves_out_siblings_to_consider = moves_out_siblings & (StockMove.browse(assigned_moves_ids) + StockMove.browse(partially_available_moves_ids))
                    reserved_moves_out_siblings = moves_out_siblings.filtered(lambda m: m.state in ['partially_available', 'assigned'])
                    move_lines_out_reserved = (reserved_moves_out_siblings | moves_out_siblings_to_consider).mapped('move_line_ids')
                    keys_out_groupby = ['location_id', 'lot_id', 'package_id', 'owner_id']
                    def _keys_out_sorted(ml):
                        return (ml.location_id.id, ml.lot_id.id, ml.package_id.id, ml.owner_id.id)

                    grouped_move_lines_out = {}
                    for k, g in groupby(sorted(move_lines_out_done, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                        qty_done = 0
                        for ml in g:
                            qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                        grouped_move_lines_out[k] = qty_done
                    for k, g in groupby(sorted(move_lines_out_reserved, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                        grouped_move_lines_out[k] = sum(self.env['stock.move.line'].concat(*list(g)).mapped('product_qty'))
                    available_move_lines = {key: grouped_move_lines_in[key] - grouped_move_lines_out.get(key, 0) for key in grouped_move_lines_in.keys()}
                    # pop key if the quantity available amount to 0
                    rounding = move.product_id.uom_id.rounding
                    available_move_lines = dict((k, v) for k, v in available_move_lines.items() if float_compare(v, 0, precision_rounding=rounding) > 0)
                    if not available_move_lines:
                        continue
                    for move_line in move.move_line_ids.filtered(lambda m: m.product_qty):
                       if available_move_lines.get((move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)):
                            available_move_lines[(move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)] -= move_line.product_qty
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
                        # `quantity` is what is brought by chained done move lines. We double check
                        # here this quantity is available on the quants themselves. If not, this
                        # could be the result of an inventory adjustment that removed totally of
                        # partially `quantity`. When this happens, we chose to reserve the maximum
                        # still available. This situation could not happen on MTS move, because in
                        # this case `quantity` is directly the quantity on the quants themselves.
                        available_quantity = move._get_available_quantity(location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
                        if float_is_zero(available_quantity, precision_rounding=rounding):
                            continue
                        quantity = move.product_uom_qty
                        taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity), location_id, lot_id, package_id, owner_id)
                        if float_is_zero(taken_quantity, precision_rounding=rounding):
                            continue
                        if float_is_zero(need - taken_quantity, precision_rounding=rounding):
                            assigned_moves_ids.add(move.id)
                            break
                        partially_available_moves_ids.add(move.id)
            if move.product_id.tracking == 'serial':
                move.next_serial_count = move.product_uom_qty
        self.env['stock.move.line'].create(move_line_vals_list)
        StockMove.browse(partially_available_moves_ids).write({'state': 'partially_available'})
        StockMove.browse(assigned_moves_ids).write({'state': 'assigned'})
        self.mapped('picking_id')._check_entire_pack()

    @api.depends('delivery_done')
    def _compute_urgent_remain_done(self):
        for record in self:
            urgent_remain_done = record.urgent_pick_inter - record.delivery_done
            if urgent_remain_done < 0:
                urgent_remain_done = 0
            record.urgent_remain_done = urgent_remain_done

    def _prepare_move_line_vals_urgen(self,qty_done,location_dest_id,lot_id):
        vals = {
            'move_id': self.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_dest_id,
            'picking_id': self.picking_id.id,
            'company_id': self.company_id.id,
            'qty_done':qty_done,
            'lot_id': lot_id,
        }
        return vals
    
    def create_move_line_urgen(self):
        deliveries = self.env['stock.picking'].search([
                ('urgent_delivery_id', '=', self.picking_id.urgent_delivery_id.id),
                ('state', '=', 'done')
            ])
        move_line_ids = self.env['stock.move.line'].search([
                ('picking_id', '=', deliveries.id),
                ('product_id', '=', self.product_id.id)
            ])
        
        dict_location_qty = {}
        location_list = []
        for location_id in self.urgent_location_ids:
            if self.picking_id.urgent_delivery_id:
                for pl_list in self.picking_id.urgent_delivery_id.picking_list_ids:
                    pl_data = self.env['picking.lists.line'].search([('picking_lists','=',pl_list.id),('product_id','=',self.product_id.id),('location_id','=',location_id.id)])
                    if pl_data:
                        if pl_data.location_id.id in dict_location_qty:
                            dict_location_qty[pl_data.location_id.id] += pl_data.qty
                        else:
                            dict_location_qty[pl_data.location_id.id] = pl_data.qty
                            location_list.append(pl_data.location_id.id)
    
        location_dest_id = self.location_dest_id._get_putaway_strategy(self.product_id).id or self.location_dest_id.id
        qty_done = self.product_uom_qty - self.urgent_pick
        if location_dest_id in dict_location_qty:
            dict_location_qty[location_dest_id] += qty_done
        else:
            dict_location_qty[location_dest_id] = qty_done
            location_list.append(location_dest_id)

        num_move_line = -1
        move_line_qty_done = 0
        qty_location = 0 
        dict_index = -1
        while num_move_line < len(move_line_ids):
            if move_line_qty_done == 0:
                num_move_line += 1
                if num_move_line < len(move_line_ids):
                    move_line_qty_done = move_line_ids[num_move_line].qty_done
                    lot_id = move_line_ids[num_move_line].lot_id
            if qty_location == 0:
                dict_index += 1
                if dict_index < len(location_list):
                    location_id = location_list[dict_index]
                    qty_location = dict_location_qty[location_id]
            if qty_location >= move_line_qty_done:
                qty_done = move_line_qty_done
            else:
                qty_done = qty_location
            move_line_qty_done -= qty_done
            qty_location -= qty_done
            if num_move_line < len(move_line_ids) and dict_index < len(location_list):
                move_line = self.env['stock.move.line'].create(self._prepare_move_line_vals_urgen(qty_done,location_id,lot_id.id))
                self.write({'move_line_ids': [(4, move_line.id)]})

    @api.onchange('product_id', 'picking_type_id')
    def onchange_product(self):
        if self.product_id:
            product = self.product_id.with_context(lang=self._get_lang())
            self.description_picking = product.name

class ReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    product_id = fields.Many2one('product.product', string="Product", required=True, domain="[('id', '=', product_id)]")
    tracking = fields.Selection(related='product_id.tracking')
    lot_ids = fields.Many2one('stock.production.lot', string='Lot/Serial')

class PickingType(models.Model):
    _inherit = "stock.picking.type"

    return_inter_picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type Inter Transfer', check_company = True)


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    
    product_return_moves = fields.One2many('stock.return.picking.line', 'wizard_id', 'Moves')
    lot_ids = fields.Many2one('stock.production.lot', string='Lots/Serials')

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id.operation_types == "Request spare parts Type":
            move_dest_exists = False
            product_return_moves = [(5,)]
            if self.picking_id and self.picking_id.state != 'ready_delivery':
                raise UserError(_("You may only return Done pickings."))
            # In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
            # default values for creation.
            line_fields = [f for f in self.env['stock.return.picking.line']._fields.keys()]
            product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(line_fields)
            for move in self.picking_id.move_lines:
                if move.state == 'cancel':
                    continue
                if move.scrapped:
                    continue
                if move.move_dest_ids:
                    move_dest_exists = True
                product_return_moves_data = dict(product_return_moves_data_tmpl)
                prepare_stock_return = self._prepare_stock_return_picking_line_vals_from_move(move)
                product_return_moves_data.update(prepare_stock_return[0])
                product_return_moves.append((0, 0, product_return_moves_data))
            if self.picking_id and not product_return_moves:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
            if self.picking_id:
                self.product_return_moves = product_return_moves
                self.move_dest_exists = move_dest_exists
                self.parent_location_id = self.picking_id.picking_type_id.warehouse_id and self.picking_id.picking_type_id.warehouse_id.view_location_id.id or self.picking_id.location_id.location_id.id
                self.original_location_id = self.picking_id.location_id.id
                location_id = self.picking_id.location_id.id
                if self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                    location_id = self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.id
                self.location_id = location_id
        else:
            move_dest_exists = False
            product_return_moves = []
            if self.picking_id and self.picking_id.state not in ('done', 'waiting_cancel') and self.picking_id.state_before_cancel != 'done':
                raise UserError(_("You may only return Done pickings."))
            # In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
            # default values for creation.
            line_fields = [f for f in self.env['stock.return.picking.line']._fields.keys()]
            
            product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(line_fields)
            for move in self.picking_id.move_lines:
                if move.state == 'cancel':
                    continue
                if move.scrapped:
                    continue
                if move.move_dest_ids:
                    move_dest_exists = True
                product_return_moves_data = dict(product_return_moves_data_tmpl)
                
                # for move_line in move.move_line_ids:
                if self.picking_id.picking_type_id.return_inter_picking_type_id.addition_operation_types.code == "AO-06" and self.picking_id.picking_type_id.code == 'internal':
                    moves = self.env["stock.move"].search([("reference", "=", move.reference),("product_id", "=", move.product_id.id),("state", "=", "cancel")])
                    line_data_list = self._prepare_stock_return_picking_line_vals_from_move(move)
                else:
                    line_data_list = self._prepare_stock_return_picking_line_vals_from_move(move)

                for line_data in line_data_list:
                    product_return_moves.append((0, 0, line_data))
                    
            if self.picking_id and not product_return_moves:
                raise UserError(
                    _("No products to return (only lines in Done state and not fully returned yet can be returned)."))
            if self.picking_id:
                self.product_return_moves = product_return_moves
                self.move_dest_exists = move_dest_exists
                self.parent_location_id = self.picking_id.picking_type_id.warehouse_id and self.picking_id.picking_type_id.warehouse_id.view_location_id.id or self.picking_id.location_id.location_id.id
                self.original_location_id = self.picking_id.location_id.id
                location_id = self.picking_id.location_id.id
                if self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                    location_id = self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.id
                self.location_id = location_id


    @api.model
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move, moves=None):
        return_lines = []
        check_loop = []

        for move_line in stock_move.move_line_ids:
            quantity = 0
            if moves:
                for s_move in moves.move_line_ids:
                    quantity += s_move.qty_done
            else:
                quantity = move_line.qty_done

            if stock_move.move_dest_ids:
                for st_dest in stock_move.move_dest_ids:
                    if st_dest.state in ('partially_available', 'assigned', 'done'):
                        check_test = False
                        for move_dest_line in st_dest.move_line_ids:
                            if move_dest_line.id in check_loop:
                                continue
    
                            if (
                                move_line.product_id.id == move_dest_line.product_id.id and
                                (
                                    (move_line.lot_id and move_dest_line.lot_id and move_line.lot_id.id == move_dest_line.lot_id.id) or
                                    (not move_line.lot_id and not move_dest_line.lot_id)
                                )
                            ):
                                if move_line.lot_id and move_dest_line.lot_id and move_line.lot_id.id == move_dest_line.lot_id.id:
                                    quantity -= move_dest_line.qty_done
                                    break
                                elif not move_line.lot_id and not move_dest_line.lot_id:
                                    check_loop.append(move_dest_line.id)
                                    if move_dest_line.id in check_loop:
                                        quantity -= move_dest_line.qty_done
                                        break
                                    
            move_line_vals = {
                'product_id': stock_move.product_id.id,
                'quantity': quantity,
                'move_id': stock_move.id,
                'uom_id': stock_move.product_id.uom_id.id,
                'lot_ids': move_line.lot_id.id if move_line.lot_id else False,
            }
            return_lines.append(move_line_vals)
        return return_lines

    def _prepare_move_default_values(self, return_line, new_picking):

        if self.picking_id.picking_type_id.return_inter_picking_type_id.addition_operation_types.code == "AO-06" and self.picking_id.picking_type_id.code == 'internal':
            if self.picking_id.picking_type_id.return_inter_picking_type_id:
                location_id = self.picking_id.picking_type_id.return_inter_picking_type_id.default_location_dest_id.id
                location_dest_id = self.location_id.id
            else:
                raise UserError(_("Please Check Operation Type Return Inter Transfer"))
        else:
            location_id = return_line.move_id.location_dest_id.id
            location_dest_id = self.location_id.id or return_line.move_id.location_id.id

        vals = {
                'product_id': return_line.product_id.id,
                'product_uom_qty': return_line.quantity,
                'product_uom': return_line.product_id.uom_id.id,
                'picking_id': new_picking.id,
                'state': 'draft',
                'date': fields.Datetime.now(),
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'lot_ids': return_line.lot_ids.ids if return_line.lot_ids else False,
                'picking_type_id': new_picking.picking_type_id.id,
                'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
                'origin_returned_move_id': return_line.move_id.id,
                'procure_method': 'make_to_stock',
            }
        
        return vals

    def _create_returns(self):
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        if self.picking_id.picking_type_id.return_inter_picking_type_id.addition_operation_types.code == "AO-06" and self.picking_id.picking_type_id.code == 'internal':
            if self.picking_id.picking_type_id.return_inter_picking_type_id:
                location_id = self.picking_id.picking_type_id.return_inter_picking_type_id.default_location_dest_id.id
            else:
                raise UserError(_("Please Check Operation Type Return Inter Transfer"))
        else:
            location_id = self.picking_id.location_dest_id.id
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id

        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': _("Return of %s", self.picking_id.name),
            'return_picking_form_id':self.picking_id.id,
            'location_id': location_id,
            'location_dest_id': self.location_id.id})
        
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self.picking_id},
            subtype_id=self.env.ref('mail.mt_note').id)
        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed."))
            # TODO sle: float_is_zero?
            if return_line.quantity:
                returned_lines += 1
                vals = self._prepare_move_default_values(return_line, new_picking)

                r = return_line.move_id.copy(vals)

                for lot_id in return_line:
                    move_line_vals = {
                        'picking_id': vals['picking_id'],
                        'product_id': vals['product_id'],
                        'product_uom_id': vals['product_uom'],
                        'qty_done': vals['product_uom_qty'],
                        'move_id': r.id,
                        'lot_id': lot_id.lot_ids.id,
                        'location_id': vals['location_id'],
                        'location_dest_id': vals['location_dest_id'],
                    }
                    self.env['stock.move.line'].create(move_line_vals)
                vals = {}

                # +--------------------------------------------------------------------------------------------------------+
                # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
                # |              | returned_move_ids              ↑                                  | returned_move_ids
                # |              ↓                                | return_line.move_id              ↓
                # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
                # +--------------------------------------------------------------------------------------------------------+
                move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')

                # link to original move
                move_orig_to_link |= return_line.move_id
                # link to siblings of original move, if any
                move_orig_to_link |= return_line.move_id\
                    .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))\
                    .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))
                move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                # link to children of originally returned moves, if any. Note that the use of
                # 'return_line.move_id.move_orig_ids.returned_move_ids.move_orig_ids.move_dest_ids'
                # instead of 'return_line.move_id.move_orig_ids.move_dest_ids' prevents linking a
                # return directly to the destination moves of its parents. However, the return of
                # the return will be linked to the destination moves.
                move_dest_to_link |= return_line.move_id.move_orig_ids.mapped('returned_move_ids')\
                    .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))\
                    .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))
                vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link]
                vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                r.write(vals)
                
                change_return = self.env['stock.move'].search([('picking_id', '=', return_line.wizard_id.picking_id.id)])
                change_state = self.env['stock.picking'].search([('id', '=', return_line.wizard_id.picking_id.id)])
                for line in change_return:
                    line.return_value += return_line.quantity
                    line.write({'return_value': line.return_value})
                    if line.return_value + line.scrap_value == change_return[0].quantity_done:
                        if change_state.state != 'waiting_cancel':
                            change_state.write({'state': 'done'})
    
        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))
  
        new_picking.action_confirm()
        new_picking.action_assign()
        
        if self.picking_id.picking_type_id.return_inter_picking_type_id.addition_operation_types.code == "AO-06" and self.picking_id.picking_type_id.code == 'internal':
            if self.picking_id.picking_type_id.return_inter_picking_type_id:
                new_picking_l_ids = self.env['stock.move.line'].search(
                    [('picking_id', '=', new_picking.id), ('reference', '=', new_picking.name), ('state', '!=', 'done')])
                
                for m_l_n in new_picking_l_ids:
                    m_l_n.write({"location_id": location_id})          
                    
                new_picking.action_assign()
        return new_picking.id, picking_type_id


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    inter_transfer_receive = fields.Many2one('stock.picking.type', string='Inter Transfer Receipt',domain=[('code','=','incoming')], check_company=True)
    inter_transfer_delivery = fields.Many2one('stock.picking.type', string='Inter Transfer Delivery',domain=[('code','=','outgoing')], check_company=True)