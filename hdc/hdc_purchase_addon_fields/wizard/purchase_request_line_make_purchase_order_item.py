# Copyright 2023 Basic Solution Co.,Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class PurchaseRequestsLineMakePurchaseOrderItem(models.TransientModel):
    _inherit = 'purchase.request.line.make.purchase.order.item'

    mix = fields.Float(string="Mix", related="orderpoint_id.product_min_qty", store=True)
    max = fields.Float(string="Max", related="orderpoint_id.product_max_qty", store=True)
    box_qty = fields.Integer(string="กล่องละ", related="product_id.product_tmpl_id.box")
    crate_qty = fields.Integer(string="ลังละ", related="product_id.product_tmpl_id.crate")

    orderpoint_id = fields.Many2one(
        'stock.warehouse.orderpoint',
        compute='_compute_orderpoint_id',
        store=True,
        string="Reordering Rule ID"
    )

    @api.depends('product_id')
    def _compute_orderpoint_id(self):
        for rec in self:
            rec.orderpoint_id = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', '=', rec.product_id.id)
            ], limit=1)
