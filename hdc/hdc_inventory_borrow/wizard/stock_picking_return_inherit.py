from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round



class ReturnPickingInherit(models.TransientModel):
    _inherit = 'stock.return.picking'
    check_done = fields.Many2one("stock.move.line")
        

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
            product_return_moves = [(5,)]
            if self.picking_id and self.picking_id.state != 'done':
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
    
    def _create_returns(self):
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
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
                change_return = self.env['stock.move'].search([('picking_id', '=', return_line.wizard_id.picking_id.id)])
                change_state = self.env['stock.picking'].search([('id', '=', return_line.wizard_id.picking_id.id)])
                for line in change_return:
                    line.return_value += return_line.quantity
                    line.write({'return_value': line.return_value })
                    if line.return_value + line.scrap_value == change_return[0].quantity_done:
                        # change_state.write({'state': 'done'})
                        return_ids = self.env['stock.picking'].search([('return_picking_form_id', '=', change_state.id)])
                        # # for line in return_ids:
                        # #     if line.state != "done":
                        # #         break
                        
                        all_done = all(pick.state == 'done' for pick in return_ids)
                        if all_done:
                            change_state.write({'state': 'done'})

        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))
        new_picking.note = self.remark
        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id
    
    def _create_rma_supplier_returns(self):
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id

        warehouse_id = self.picking_id.picking_type_id.warehouse_id.id
        
        check_addition_operation_type = self.env['addition.operation.type'].search(
            [('code', '=', "AO-09")], limit=1
        )
        
        check_supplier_type = self.env['stock.picking.type'].search(
            [('addition_operation_types', '=', check_addition_operation_type.id) , ('warehouse_id', '=', warehouse_id)], limit=1
        )

        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': check_supplier_type.id if check_supplier_type else picking_type_id,
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
                change_return = self.env['stock.move'].search([('picking_id', '=', return_line.wizard_id.picking_id.id)])
                change_state = self.env['stock.picking'].search([('id', '=', return_line.wizard_id.picking_id.id)])
                for line in change_return:
                    line.return_value += return_line.quantity
                    line.write({'return_value': line.return_value })
                    if line.return_value + line.scrap_value == change_return[0].quantity_done:
                        # change_state.write({'state': 'done'})
                        return_ids = self.env['stock.picking'].search([('return_picking_form_id', '=', change_state.id)])
                        # # for line in return_ids:
                        # #     if line.state != "done":
                        # #         break
                        
                        all_done = all(pick.state == 'done' for pick in return_ids)
                        if all_done:
                            change_state.write({'state': 'done'})

        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id

        
            