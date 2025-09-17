# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models,_
from odoo.tools.misc import clean_context
from odoo.exceptions import UserError
from odoo.tools import float_compare

class RepairOrder(models.Model):
    _inherit = "repair.order"

    purchase_claim_id = fields.Many2one('purchase.crm.claim.ept', string='Claim')
    picking_ids = fields.Many2many('stock.picking', string="Picking")

    def action_repair_done(self):
        """Inherit this method for checking created repair order is from claim"""
        if self.purchase_claim_id:
            result = super().action_repair_done()
            if self.purchase_claim_id and self.purchase_claim_id.return_picking_id:
                self.repair_action_launch_stock_rule()
            return result
        else:
            if self.claim_id and self.claim_id.return_picking_id:
                # if self.claim_id.rma_type == 'receive_modify' and self.claim_id.is_dewalt and self.claim_id.warranty_type != 'out':
                if self.claim_id.rma_type == 'receive_modify' and self.claim_id.is_dewalt:
                    result = self.action_repair_done_new()
                else:
                    result = super().action_repair_done()
                self.repair_action_launch_stock_rule()
            else:
                result = super().action_repair_done()
            return result

    def action_repair_done_new(self):
        """ Creates stock move for operation and stock move for final product of repair order.
        @return: Move ids of final products

        """
        if self.filtered(lambda repair: not repair.repaired):
            raise UserError(_("Repair must be repaired in order to make the product moves."))
        self._check_company()
        self.operations._check_company()
        self.fees_lines._check_company()
        res = {}
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        Move = self.env['stock.move']
        for repair in self:
            # Try to create move with the appropriate owner
            owner_id = False
            available_qty_owner = self.env['stock.quant']._get_available_quantity(repair.product_id, repair.location_id, repair.lot_id, owner_id=repair.partner_id, strict=True)
            if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                owner_id = repair.partner_id.id

            moves = self.env['stock.move']
            operations_lines = repair.operations
            # if repair.claim_id.rma_type == 'receive_modify' and repair.claim_id.is_dewalt and repair.claim_id.warranty_type != 'out':
            if repair.claim_id.rma_type == 'receive_modify' and repair.claim_id.is_dewalt:
                operations_lines = operations_lines.filtered(lambda x: x.type == 'remove')
            for operation in operations_lines:
                move = Move.create({
                    'name': repair.name,
                    'product_id': operation.product_id.id,
                    'product_uom_qty': operation.product_uom_qty,
                    'product_uom': operation.product_uom.id,
                    'partner_id': repair.address_id.id,
                    'location_id': operation.location_id.id,
                    'location_dest_id': operation.location_dest_id.id,
                    'repair_id': repair.id,
                    'origin': repair.name,
                    'company_id': repair.company_id.id,
                })

                # Best effort to reserve the product in a (sub)-location where it is available
                product_qty = move.product_uom._compute_quantity(
                    operation.product_uom_qty, move.product_id.uom_id, rounding_method='HALF-UP')
                available_quantity = self.env['stock.quant']._get_available_quantity(
                    move.product_id,
                    move.location_id,
                    lot_id=operation.lot_id,
                    strict=False,
                )
                move._update_reserved_quantity(
                    product_qty,
                    available_quantity,
                    move.location_id,
                    lot_id=operation.lot_id,
                    strict=False,
                )
                # Then, set the quantity done. If the required quantity was not reserved, negative
                # quant is created in operation.location_id.
                move._set_quantity_done(operation.product_uom_qty)

                if operation.lot_id:
                    move.move_line_ids.lot_id = operation.lot_id

                moves |= move
                operation.write({'move_id': move.id, 'state': 'done'})
            move = Move.create({
                'name': repair.name,
                'product_id': repair.product_id.id,
                'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                'product_uom_qty': repair.product_qty,
                'partner_id': repair.address_id.id,
                'location_id': repair.location_id.id,
                'location_dest_id': repair.location_id.id,
                'move_line_ids': [(0, 0, {'product_id': repair.product_id.id,
                                           'lot_id': repair.lot_id.id,
                                           'product_uom_qty': 0,  # bypass reservation here
                                           'product_uom_id': repair.product_uom.id or repair.product_id.uom_id.id,
                                           'qty_done': repair.product_qty,
                                           'package_id': False,
                                           'result_package_id': False,
                                           'owner_id': owner_id,
                                           'location_id': repair.location_id.id, #TODO: owner stuff
                                           'company_id': repair.company_id.id,
                                           'location_dest_id': repair.location_id.id,})],
                'repair_id': repair.id,
                'origin': repair.name,
                'company_id': repair.company_id.id,
            })
            consumed_lines = moves.mapped('move_line_ids')
            produced_lines = move.move_line_ids
            moves |= move
            moves._action_done()
            produced_lines.write({'consume_line_ids': [(6, 0, consumed_lines.ids)]})
            res[repair.id] = move.id
        return res

    # def action_repair_done(self):
    #     """Inherit this method for checking created repair order is from claim"""
    #     result = super().action_repair_done()
    #     if self.claim_id and self.claim_id.return_picking_id:
    #         self.repair_action_launch_stock_rule()
    #     return result

    def repair_action_launch_stock_rule(self):
        """based on this method to create a picking one..two or three step."""
        procurements = []
        picking_vals = {}

        vals = self._prepare_procurement_group_vals()
        group_id = self.env['procurement.group'].create(vals)

        values = self._prepare_procurement_values(group_id)
        if self.purchase_claim_id:
            location_id = self.purchase_claim_id.partner_delivery_id.property_stock_customer

            procurements.append(self.env['procurement.group'].Procurement(
            self.product_id, self.product_qty, self.product_id.uom_id,
            location_id, self.name, self.purchase_claim_id.name, self.company_id, values))
        else:
            location_id = self.claim_id.partner_delivery_id.property_stock_customer

            procurements.append(self.env['procurement.group'].Procurement(
            self.product_id, self.product_qty, self.product_id.uom_id,
            location_id, self.name, self.claim_id.name, self.company_id, values))

        # procurements.append(self.env['procurement.group'].Procurement(
        #     self.product_id, self.product_qty, self.product_id.uom_id,
        #     location_id, self.name, self.purchase_claim_id.name, self.company_id, values))

        if procurements:
            self.env['procurement.group'].with_context(clean_context(self.env.context)).run(
                procurements)

        pickings = self.env['stock.picking'].search([('group_id', '=', group_id.id)])
        picking_ids = self.picking_ids.ids + pickings.ids
        picking = pickings[-1]

        if picking.location_id.id != self.location_id.id:
            picking_vals.update({'location_id':self.location_id.id})
            picking.write({'location_id':self.location_id.id})
            picking.action_assign()
            move_line = picking.move_line_ids_without_package

            if self.lot_id and move_line and move_line.lot_id.id != self.lot_id.id:
                picking.move_line_ids_without_package.write({'lot_id':self.lot_id.id})

        self.write({'picking_ids':[(6, 0, picking_ids)]})

    def _prepare_procurement_values(self, group_id):
        """prepare values for procurement"""
        if self.purchase_claim_id:
            return {
                'group_id':group_id,
                'warehouse_id':self.purchase_claim_id.purchase_id.warehouse_id or False,
                'partner_id':self.address_id.id,
                'company_id':self.company_id,
                'repair_order_id':self.id,
            }
        else:
            if self.claim_id.sale_id:
                warehouse_id = self.claim_id.sale_id.warehouse_id
            else:
                if self.claim_id.rma_reason_id:
                    if self.claim_id.rma_reason_id.operation_type_delivery_id:
                        warehouse_id = self.claim_id.rma_reason_id.operation_type_delivery_id.warehouse_id
                    else:
                        raise UserError(_("Please Check Operation Type In RMA Reason Delivery"))
            if self.claim_id.is_dewalt:
                if self.repair_type_id.borrow_picking_type_id :
                    warehouse_id = self.repair_type_id.borrow_picking_type_id.warehouse_id
                else:
                    raise UserError(_("Please Check Operation Type In RMA Reason"))
            return {
                'group_id':group_id,
                'warehouse_id':warehouse_id or False,
                'partner_id':self.address_id.id,
                'company_id':self.company_id,
                'repair_order_id':self.id,
                }

    def _prepare_procurement_group_vals(self):
        """prepare a procurement group vals."""
        if self.purchase_claim_id:
            return {
                'name':self.name,
                'partner_id':self.purchase_claim_id.partner_delivery_id.id,
                'move_type':self.purchase_claim_id.purchase_id.picking_policy or 'direct',
            }
        else:
            return {
            'name':self.name,
            'partner_id':self.claim_id.partner_delivery_id.id,
            'move_type':self.claim_id.sale_id.picking_policy or 'direct',
        }

    def show_delivery_picking(self):
        """display the delivery orders on RMA."""
        if len(self.picking_ids) == 1:
            picking_action = {
                'name':"Delivery",
                'view_mode':'form',
                'res_model':'stock.picking',
                'type':'ir.actions.act_window',
                'res_id':self.picking_ids.id
            }
        else:
            picking_action = {
                'name':"Deliveries",
                'view_mode':'tree,form',
                'res_model':'stock.picking',
                'type':'ir.actions.act_window',
                'domain':[('id', 'in', self.picking_ids.ids)]
            }
        return picking_action
