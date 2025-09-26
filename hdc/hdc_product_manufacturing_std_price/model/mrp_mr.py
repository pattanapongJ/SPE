# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools.misc import clean_context

class MRPMR(models.Model):
    _inherit = 'mrp.mr'
    order_list = fields.One2many('mr.order.list', 'mr_id',store=True,compute="_compute_order_list",)
    amount_order_list = fields.Float(string="Amount",compute="_compute_total_amount_order_list")

    @api.depends('order_list')
    def _compute_total_amount_order_list(self):
        for record in self:
            record.amount_order_list = sum(line.subtotal for line in record.order_list)

    @api.depends('product_line_ids')
    def _compute_order_list(self):
        for record in self:
            existing_order_ids = record.order_list.ids
            if existing_order_ids:
                record.order_list.unlink()
            new_order_lines = [(0, 0, {
                'product_id': line.product_id.id,
                'demand_qty': line.demand_qty,
                'uom_id': line.uom_id.id,
                'factory_cost': line.factory_price
            }) for line in record.product_line_ids if line.product_id]
            record.order_list = new_order_lines

class MROrderList(models.Model):
    _name = 'mr.order.list'
    _description = 'MR Order List'

    mr_id = fields.Many2one('mrp.mr', string='mr_id', ondelete='cascade')
    product_id = fields.Many2one("product.product", string="Product",readonly=True)
    demand_qty = fields.Float("Quality",readonly=True)
    uom_id = fields.Many2one("uom.uom", string="UOM",readonly=True)
    factory_cost = fields.Float(string="Factory Cost")
    subtotal = fields.Float(string="Subtotal",compute="_compute_subtotal")

    @api.depends('demand_qty','factory_cost')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.demand_qty * record.factory_cost
    
