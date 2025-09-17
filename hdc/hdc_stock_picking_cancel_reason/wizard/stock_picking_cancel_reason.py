# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo import fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round

class StockPickingCancel(models.TransientModel):
    _name = "stock.picking.cancel"
    _description = "Stock Picking Cancel"

    reason_id = fields.Many2one(
        comodel_name="stock.picking.cancel.reason", string="Reason", required=True
    )
    description = fields.Text(string="Description")

    def confirm_cancel(self):
        self.ensure_one()
        act_close = {"type": "ir.actions.act_window_close"}
        picking_ids = self._context.get("active_ids")
        if picking_ids is None:
            return act_close
        assert len(picking_ids) == 1, "Only 1 picking ID expected"
        picking = self.env["stock.picking"].browse(picking_ids)
        # for re in picking_ids:
        check_return = 0
        for stock_move in picking.move_lines:
            quantity = stock_move.product_qty
            for move in stock_move.move_dest_ids:
                if not move.origin_returned_move_id or move.origin_returned_move_id != stock_move:
                    continue
                if move.state in ('partially_available', 'assigned'):
                    quantity -= sum(move.move_line_ids.mapped('product_qty'))
                elif move.state in ('done'):
                    quantity -= move.product_qty
            quantity = float_round(quantity, precision_rounding=stock_move.product_id.uom_id.rounding)
            if quantity > 0:
                check_return+=1
        if picking.state == 'done':
            if check_return > 0 :
                raise ValidationError(_("You cannot cancel a stock move that has been set to 'Done'.  Create a return in order to reverse the moves which took place."))
        
        picking.write(
            {
                "cancel_reason_id": self.reason_id.id,
                "cancel_description": self.description,
            }
        )
        now_state_picking = picking.state
        if now_state_picking == "done":
            picking.write({ "state": "skip_done"})
            for move in picking.move_ids_without_package:
                move.state = "skip_done"
        if picking.state_before_cancel == 'done':
            for line in picking.move_lines:
                check_done = 0
                for move in line.move_dest_ids.filtered(lambda m: m.state in ('done')):
                    check_done += move.product_uom_qty
                if line.product_uom_qty != check_done:
                    picking.action_cancel()
            picking.state = 'cancel'
            for pick in picking.sale_id.picking_ids:
                if pick.state != 'cancel' and pick.return_picking_form_id is False:
                    return act_close
                # picking.sale_id.state = 'cancel'
                picking.sale_id.action_cancel()
            return act_close

        # if picking.origin:
        #     inter_picking_ids_head = self.env['stock.picking'].search([('name', '=', picking.origin)], limit=1)
        #     if inter_picking_ids_head.addition_operation_types.code == "AO-06":
        #         # if inter_picking_ids_head.backorder_id:
        #         #     for inter in inter_picking_ids.filtered(lambda it: it.state == 'done'):
        #         #         if inter.backorder_id:
        #         #             raise ValidationError(_("Cancellation cannot be made because the product has already been shipped to the destination."))
        #         #     for inter in inter_picking_ids.filtered(lambda it: it.state not in ('done', 'cancel')):
        #         #         if inter.backorder_id:
        #         #             inter.action_cancel()
        #         # else:
        #         inter_picking_ids = self.env['stock.picking'].search([('origin', '=', inter_picking_ids_head.name)])
        #         for inter in inter_picking_ids.filtered(lambda it: it.state == 'done'):
        #             language = self.env.context.get('lang')
        #             if language == 'th_TH':
        #                 raise ValidationError(_("ไม่สามารถยกเลิกได้เนื่องจากปลายทางมีการจัดส่งสินค้าแล้ว."))
        #             else:
        #                 raise ValidationError(_("Cancellation cannot be made because the product has already been shipped to the destination."))
        #         for inter in inter_picking_ids.filtered(lambda it: it.state not in ('done', 'cancel')):
        #             inter.action_cancel()
        #     inter_picking_ids_head.inter_state = 'cancel'

        if picking.inter_state == 'delivery':
            inter_picking_ids = self.env['stock.picking'].search([('origin', '=', picking.name)])
            for inter in inter_picking_ids:
                if inter.state not in ('done', 'cancel'):
                    inter.action_cancel()
                # if inter.state != "cancel":
                #     return act_close

            picking.inter_state = 'cancel'
            picking.action_cancel()
            return act_close

        picking.action_cancel()
        for pick in picking.sale_id.picking_ids:
            if pick.state != 'cancel':
                return act_close
        # picking.sale_id.state = 'cancel'
        picking.sale_id.action_cancel()
        return act_close
