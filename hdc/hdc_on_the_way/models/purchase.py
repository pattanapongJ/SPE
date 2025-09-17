# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    stock_moves = fields.One2many(
        'stock.move',
        string='Stock Moves',
        compute='_compute_stock_moves'
    )

    @api.depends('stock_moves', 'state')
    def _compute_stock_moves(self):
        for purchase in self:
            purchase_stock_moves = self.env['stock.move'].search([('origin', '=', purchase.name)])
            on_the_way =[]
            for stock_move_ids in purchase_stock_moves:
                on_the_way.append(stock_move_ids.id)
            if purchase_stock_moves: 
                purchase.stock_moves = on_the_way
            else :
                purchase.stock_moves = False

