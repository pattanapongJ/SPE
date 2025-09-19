# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class ReturnRepairOrder(models.TransientModel):
    _name = "return.repair.order.line"
    _rec_name = 'product_id'
    _description = 'Return repair order Line'

    product_id = fields.Many2one('product.product', string="Product", required=True, domain="[('id', '=', product_id)]")
    quantity = fields.Float("Quantity", digits='Product Unit of Measure', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='move_id.product_uom', readonly=False)
    wizard_id = fields.Many2one('return.repair.order', string="Wizard")
    move_id = fields.Many2one('stock.move', "Move")
    to_refund = fields.Boolean(string="Update quantities on SO/PO", copy=False,
                               help='Trigger a decrease of the delivered/received quantity in the associated Sale Order/Purchase Order')
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial',
        domain="[('product_id','=', product_id)]", check_company=True,
        help="Products repaired are all belonging to this lot", required=True)

class ReturnRepairOrder(models.TransientModel):
    _name = 'return.repair.order'
    _description = 'Return repair order'

    @api.model
    def default_get(self, fields):
        if len(self.env.context.get('active_ids', list())) > 1:
            raise UserError(_("You may only return one picking at a time."))
        res = super(ReturnRepairOrder, self).default_get(fields)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'stock.picking':
            picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            if picking.exists():
                res.update({'picking_id': picking.id})
        return res

    picking_id = fields.Many2one('stock.picking')
    product_return_moves = fields.One2many('return.repair.order.line', 'wizard_id', 'Moves')
    company_id = fields.Many2one(related='picking_id.company_id')
    move_dest_exists = fields.Boolean('Chained Move Exists' , readonly=True)

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        move_dest_exists = False
        product_return_moves = [(5 ,)]
        product_return_moves_data = []
        line_fields = [f for f in self.env['return.repair.order.line']._fields.keys()]
        product_return_moves_data_tmpl = self.env['return.repair.order.line'].default_get(line_fields)
        for move in self.picking_id.move_lines:
            if move.state == 'cancel':
                continue
            if move.scrapped:
                continue
            if move.move_dest_ids:
                move_dest_exists = True
            data_move = self._prepare_stock_return_picking_line_vals_from_move(move)
            if data_move:
                product_return_moves_data = dict(product_return_moves_data_tmpl)
                product_return_moves_data.update(data_move)
                product_return_moves.append((0 , 0 , product_return_moves_data))
        if not product_return_moves_data:
            raise UserError(_("No products to Repair"))
        if self.picking_id:
            self.product_return_moves = product_return_moves
            self.move_dest_exists = move_dest_exists

    @api.model
    def _prepare_stock_return_picking_line_vals_from_move(self , stock_move):
        quantity = stock_move.product_qty
        quantity_sum = 0
        rp_order = self.env['repair.order'].search([('product_id', '=', stock_move.product_id.id), ('requisition_id', '=' , self.picking_id.id)])
        if rp_order:
            quantity_sum = quantity
            for rp_line in rp_order:
                quantity_sum -= rp_line.product_qty
            if quantity_sum > 0:
                return {
                    'product_id': stock_move.product_id.id ,
                    'quantity': quantity_sum,
                    'move_id': stock_move.id ,
                    'uom_id': stock_move.product_id.uom_id.id
                }
            else:
                return {}
        else:
            return {
                'product_id': stock_move.product_id.id ,
                'quantity': quantity ,
                'move_id': stock_move.id ,
                'uom_id': stock_move.product_id.uom_id.id
            }

    def create_returns(self):
        for line in self.product_return_moves:
            values = {
                'product_id': line.product_id.id ,
                'product_qty': line.quantity,
                'product_uom': line.uom_id.id,
                'requisition_id': self.picking_id.id,
                'lot_id': line.lot_id.id,
                'location_id': line.move_id.location_id.id
            }
            self.env["repair.order"].create(values)