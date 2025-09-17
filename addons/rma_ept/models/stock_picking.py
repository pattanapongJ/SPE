# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    claim_count_out = fields.Integer(compute='_compute_claim_count_out', string="Claim Count")
    claim_id = fields.Many2one('crm.claim.ept', string="RMA Claim", copy=False, store=True)
    rma_sale_id = fields.Many2one('sale.order', string="Rma Sale Order", copy=False)
    repair_order_id = fields.Many2one('repair.order', string="Repair Order", copy=False)
    view_claim_button = fields.Boolean(compute='_compute_view_claim_button')
    rma_reason_id = fields.Many2one(related = 'claim_id.rma_reason_id',depends = ["claim_id"], store = True,string="RMA Customer Reason")

    def _compute_claim_count_out(self):
        """
        This method used to display the number of a claim for related picking.
        """
        for record in self:
            record.claim_count_out = self.env['crm.claim.ept'].search_count \
                ([('picking_id', '=', record.id)])

    def _compute_view_claim_button(self):
        """
        This method used to display a claim button on the picking based on the picking stage.
        """
        for record in self:
            record.view_claim_button = False
            if record.sale_id and record.state == 'done' and \
                    record.picking_type_code in ( \
                    'outgoing', 'internal'):
                record.view_claim_button = True

    def write(self, vals):
        """
        This methos is used to write state of related claim.
        """
        for record in self.filtered(lambda l: l.state == 'done' and \
                                    l.picking_type_code == 'incoming' and l.claim_id and \
                                    l.claim_id.state == 'approve'):
            record.claim_id.write({'state':'process'})
        
        for record in self.filtered(lambda l: l.state == 'done' and \
                                    l.picking_type_code == 'incoming' and l.claim_id and \
                                    l.claim_id.is_not_receipt and l.claim_id.state == 'process'):
            record.claim_id.write({'state':'close'})

        return super().write(vals)

class ReturnPickingInherit(models.TransientModel):
    _inherit = 'stock.return.picking'
    
    
    def _create_rma_returns(self):
        # new_picking, pick_type_id = super(ReturnPickingInherit, self)._create_returns()
        
        warehouse_id = self.picking_id.picking_type_id.warehouse_id.id
        
        check_addition_operation_type = self.env['addition.operation.type'].search(
            [('code', '=', "AO-05")], limit=1
        )
        
        check_return_customer = self.env['stock.picking.type'].search(
            [('addition_operation_types', '=', check_addition_operation_type.id) , ('warehouse_id', '=', warehouse_id)], limit=1
        )
        
        if not check_return_customer:
            raise UserError(_("Please Check Operation Type Return Customer"))


        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id

        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': check_return_customer.id,
            'state': 'draft',
            'origin': _("Return of %s", self.picking_id.name),
            'return_picking_form_id':self.picking_id.id,
            'location_id': self.picking_id.location_dest_id.id,
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
        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id
    