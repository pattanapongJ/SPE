# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools.float_utils import float_is_zero
from itertools import groupby

class Picking(models.Model):
    _inherit = "stock.picking"

    currency_id = fields.Many2one(related='purchase_id.currency_id', store=True, string='Purchase Currency', readonly=True)
    amount_untaxed = fields.Monetary(string='Untaxed', store=False, readonly=True, compute='_amount_all', tracking=True)
    amount_tax = fields.Monetary(string='Vat', store=False, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=False, readonly=True, compute='_amount_all')
    picking_origin_split_id = fields.Many2one(comodel_name="stock.picking",string="Split Receipt From")
    invoice_date = fields.Datetime(string='Invoice Date')
    invoice_no = fields.Char(string="Invoice No.")
    
    @api.depends('move_ids_without_package.gross_unit_price','move_ids_without_package.product_uom_qty')
    def _amount_all(self):
        for rec in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            amount_total = 0.0
            if rec.purchase_id and rec.picking_type_code == 'incoming':
                for line in rec.move_ids_without_package:
                    line_amount_untaxed = line.subtotal
                    line_amount_tax = line.price_tax
                    line_amount_total = line.net_price
                    
                    amount_untaxed += line_amount_untaxed
                    amount_tax += line_amount_tax
                    amount_total += line_amount_total

            rec.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_total,
            })

    def action_split_receipt_in(self):
        product_line_ids = []
        allowed_product_ids = []
        for line in self.move_ids_without_package:
            demand = line.product_uom_qty
            if demand > 0:
                    line_data = (0, 0, {
                        'move_id': line.id,
                        'currency_id': line.currency_id.id,
                        'price_unit': line.price_unit,
                        'taxes_id': line.taxes_id.ids,
                        'product_id': line.product_id.id,
                        'location_id': line.location_id.id,
                        'po_remain': line.po_remain,
                        'po_receive_qty': line.po_remain,
                        'po_product_uom': line.po_product_uom.id,
                        'product_uom_qty': demand,
                        'receive_qty': demand,
                        'product_uom': line.product_uom.id,
                    })
                    product_line_ids.append(line_data)
                    allowed_product_ids.append(line.product_id.id)
        context = {
            'default_picking_id': self.id,
            'default_location_id': self.location_id.id,
            'default_product_line_ids': product_line_ids,
            'allowed_product_ids': allowed_product_ids,
            'default_picking_type_id': self.picking_type_id.id,
            'default_currency_id': self.currency_id.id,
        }
        return {
                'type': 'ir.actions.act_window',
                'name': 'Add : Choose Products Receipts',
                'res_model': 'wizard.split.receipt.in',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    def write(self, vals):
        res = super(Picking, self).write(vals)
        if vals.get('location_dest_id'):
            if self.purchase_id and self.picking_type_code == 'incoming' and self.state in ['draft','confirmed','assigned']:
                for move in self.move_ids_without_package:
                    for line in move.move_line_nosuggest_ids:
                        line.update({
                            'location_dest_id': self.location_dest_id,
                        })
        return res