# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models, tools, _
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time

class StockValuationLayer(models.Model):
    _name = 'stock.valuation.layer'
    _inherit = ['stock.valuation.layer','mail.thread', 'mail.activity.mixin']

    new_date_cost = fields.Datetime(string="Date Cost",copy=False)
    cal_date_cost = fields.Datetime(string="Date Cost", compute="_compute_cal_date_cost",store=True, index=True)
    picking_type_id = fields.Many2one('stock.picking.type', string="Picking Type", related="stock_move_id.picking_type_id", store=True)

    @api.depends("create_date", "new_date_cost")
    def _compute_cal_date_cost(self):
        for line in self:
            line.cal_date_cost = line.new_date_cost if line.new_date_cost else line.create_date


class stock_inventory(models.Model):
    _inherit = 'stock.inventory'

    new_date_cost = fields.Datetime(string="Date Cost", copy=False)

class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        self.ensure_one()
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'new_date_cost': self.inventory_id.new_date_cost,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': qty,
            'date': self.inventory_id.date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'confirmed',
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'lot_id': self.prod_lot_id.id,
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': qty,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
            })]
        }



