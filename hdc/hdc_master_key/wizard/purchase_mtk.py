# -*- coding: utf-8 -*-
import base64
import io
from odoo import models, fields, api

class WizardPurchaseMTK(models.TransientModel):
    _name = "wizard.purchase.mtk"
    _description = "Wizard for Editing Purchase Order Lines"

    purchase_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    line_ids = fields.One2many('wizard.purchase.mtk.line', 'wizard_id', string='Purchase Lines')

    @api.model
    def default_get(self, fields):
        res = super(WizardPurchaseMTK, self).default_get(fields)
        if self.env.context.get('active_id'):
            purchase = self.env['purchase.order'].browse(self.env.context['active_id'])
            res['purchase_id'] = purchase.id
            lines = []
            for line in purchase.order_line:
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'description': line.name,
                    'gross_unit_price': line.gross_unit_price,
                    'quantity': line.product_qty,
                    'purchase_line_id': line.id
                }))
            res['line_ids'] = lines
        return res

    def apply_changes(self):
        for line in self.line_ids:
            order_line = self.env['purchase.order.line'].browse(line.purchase_line_id.id)
            order_line.write({
                'name': line.description,
                'gross_unit_price': line.gross_unit_price
            })

            if order_line.product_id:
                stock_moves = self.env['stock.move'].search([
                    ('purchase_line_id', '=', order_line.id),
                    ('state', '!=', 'cancel')
                ])

                old_gross_unit_price = line.gross_unit_price
                for move in stock_moves:
                    for move_line in move.move_line_ids:
                        valuation_layers = self.env['stock.valuation.layer'].search([
                            ('stock_move_id', '=', move.id)
                        ])

                        for valuation in valuation_layers:
                            new_value = (line.gross_unit_price * move_line.qty_done)
                            old_value = (old_gross_unit_price * move_line.qty_done)
                            diff_value = new_value - old_value
                            valuation.write({
                                'unit_cost': line.gross_unit_price,
                                'value': line.gross_unit_price,
                                #'value': valuation.value + diff_value
                            })


class WizardPurchaseMTKLine(models.TransientModel):
    _name = "wizard.purchase.mtk.line"
    _description = "Editable Purchase Order Line in Wizard"

    wizard_id = fields.Many2one('wizard.purchase.mtk', string='Wizard Reference', required=True)
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    description = fields.Text(string='Description')
    gross_unit_price = fields.Float(string='Unit Price')
    quantity = fields.Float(string='Quantity', readonly=True)
