# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class PickingType(models.Model):
    _inherit = "stock.picking.type"

    is_oversea = fields.Boolean(string='Is Oversea')
    is_local = fields.Boolean(string='Is Local')
    
class StockMove(models.Model):
    _inherit = 'stock.move'
    
    receipt_list_line_id = fields.One2many('receipt.list.line', 'move_id', string='Receipt List line')
    demand_total = fields.Float(related='purchase_line_id.product_qty', string='PO Total Demand',digits='Product Unit of Measure',)

    origin_rl_move_id = fields.Many2one(
        'stock.move', 'Origin RL move', copy=False, index=True,
        help='Move that created the RL move', check_company=True)
    rl_move_ids = fields.One2many('stock.move', 'origin_rl_move_id', 'All RL moves', help='Optional: all RL moves created from this move')

    gross_unit_price = fields.Float(related='purchase_line_id.gross_unit_price', string="Purchase Unit Price", digits='Product Price',default=0)
    taxes_id = fields.Many2many(related='purchase_line_id.taxes_id', string='Purchase Taxes')
    po_product_uom = fields.Many2one(related='purchase_line_id.product_uom', string='PO Unit of Measure')
    po_remain = fields.Float(compute='_compute_po_remain', string="PO Demand")
    po_qty_counted = fields.Float("PO Shipped", digits='Product Unit of Measure',copy=False)
    po_reserve = fields.Float(compute='_compute_po_reserve', string="PO Reserve")
    po_quantity_done = fields.Float(compute='_compute_po_qty_done', string="PO Done")
    subtotal = fields.Monetary(compute='_compute_amount', string="Subtotal")
    price_tax = fields.Float(compute='_compute_amount', string='Tax')
    net_price = fields.Monetary(compute='_compute_amount', string="Net Price")

    def convert_uom_factor(self, product=False, qty=0, move_po_uom=False):

        if not (product and qty and move_po_uom):
            qty = 0
            return qty

        base_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_type == "base" and l.product_id.id == product.id
        )
        if not base_map:  # ตรวจว่ามี factor, uom ที่ base มั้ย
            qty = 0
            return qty
        
        base_uom = base_map[0].uom_id

        po_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_id.id == move_po_uom.id and l.product_id.id == product.id
        )
        if (
            not po_map or not po_map[0].factor_base
        ):  # ตรวจว่ามี factor, uom ที่เราส่งมามั้ย
            qty = 0
            sale_line_uom = False
            return qty, sale_line_uom

        factor = po_map[0].factor_base
        product_qty_f = qty * factor

        return product_qty_f
    
    def convert_uom_factor_po(self, product=False, qty=0, move_po_uom=False):
        po_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_id.id == move_po_uom.id and l.product_id.id == product.id
        )
        if (
            not po_map or not po_map[0].factor_base
        ):  # ตรวจว่ามี factor, uom ที่เราส่งมามั้ย
            qty = 0
            return qty

        factor = po_map[0].factor_base
        if factor != 0:
            product_qty_f = qty / factor
        else:
            product_qty_f = 0

        return product_qty_f
    
    def _compute_po_remain(self):
        for move in self:
            if move.purchase_line_id:
                product_qty_f = move.product_uom_qty
                if move.po_product_uom.id != move.product_uom.id:
                    product_qty_f = move.convert_uom_factor_po(
                        move.product_id, move.product_uom_qty, move.po_product_uom
                    )
                move.po_remain = product_qty_f
            else:
                move.po_remain = 0

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        res.po_qty_counted = res.po_remain
        return res

    @api.onchange("po_qty_counted")
    def _onchange_po_qty_counted(self):
        if not self.env.context.get('from_qty_counted'):
            self = self.with_context(from_po_qty_counted=True)
            product_qty_f = self.po_qty_counted
            if self.po_product_uom.id != self.product_uom.id:
                product_qty_f = self.convert_uom_factor(
                        self.product_id, self.po_qty_counted, self.po_product_uom
                    )
            self.qty_counted = product_qty_f

    @api.onchange("qty_counted")
    def _onchange_qty_counted_po_qty_counted(self):
        if self.picking_id.purchase_id and self.picking_id.picking_type_code == 'incoming':
            if not self.env.context.get('from_po_qty_counted'):
                self = self.with_context(from_qty_counted=True)
                product_qty_f = self.qty_counted
                if self.po_product_uom.id != self.product_uom.id:
                    product_qty_f = self.convert_uom_factor_po(
                            self.product_id, self.qty_counted, self.po_product_uom
                        )
                self.po_qty_counted = product_qty_f

    def _compute_po_reserve(self):
        for move in self:
            if move.purchase_line_id:
                product_qty_f = move.reserved_availability
                if move.po_product_uom.id != move.product_uom.id:
                    product_qty_f = move.convert_uom_factor_po(
                        move.product_id, move.reserved_availability, move.po_product_uom
                    )
                move.po_reserve = product_qty_f
            else:
                move.po_reserve = 0

    def _compute_po_qty_done(self):
        for move in self:
            if move.purchase_line_id:
                product_qty_f = move.quantity_done
                if move.po_product_uom.id != move.product_uom.id:
                    product_qty_f = move.convert_uom_factor_po(
                        move.product_id, move.quantity_done, move.po_product_uom
                    )
                move.po_quantity_done = product_qty_f
            else:
                move.po_quantity_done = 0

    def _prepare_compute_all_values(self):
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency_id': self.currency_id,
            'product_qty': self.po_qty_counted,
            'product': self.product_id,
            'partner': self.picking_id.partner_id,
        }
    
    @api.depends('price_unit', 'po_qty_counted', 'taxes_id','picking_id.purchase_id')
    def _compute_amount(self):
        for line in self:
            if line.picking_id.purchase_id:
                vals = line._prepare_compute_all_values()
                taxes = line.taxes_id.compute_all(
                    vals['price_unit'],
                    vals['currency_id'],
                    vals['product_qty'],
                    vals['product'],
                    vals['partner'])
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'net_price': taxes['total_included'],
                    'subtotal': taxes['total_excluded'],
                })
            else:
                line.update({
                    'price_tax': 0,
                    'net_price': 0,
                    'subtotal': 0,
                })

    def update_po_qty_counted(self):
        domain = [('purchase_line_id', '!=', False),('picking_id.picking_type_code', '=', 'incoming')]
        move_line = self.env['stock.move'].search(domain)

        for line in move_line:
            if line.po_product_uom.id == line.product_uom.id:
                line = line.with_context(from_qty_counted=True)
                line.po_qty_counted = line.qty_counted
            else:
                line = line.with_context(from_qty_counted=True)
                po_qty_counted = line.convert_uom_factor_po(
                    line.product_id, line.qty_counted, line.po_product_uom
                )
                line.po_qty_counted = po_qty_counted

    def _action_confirm(self, merge=True, merge_into=False):
        """ override _action_confirm
        """
        if self.receipt_list_line_id:
            merge = False
        result = super()._action_confirm(merge,merge_into)
        return result
    
    def update_receipt_description_picking_po(self):
        domain = [('purchase_line_id', '!=', False),('picking_id.picking_type_code', '=', 'incoming')]
        move_line = self.env['stock.move'].search(domain)
        for line in move_line:
            line.description_picking = line.purchase_line_id.name