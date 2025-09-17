from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _

import traceback

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"    
    
class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    sale_id = fields.Many2one('sale.order')

    @api.onchange('picking_list')
    def onchange_picking_list(self):
        domain = []
        if self.picking_list:
            lines = []
            if self.advance_payment_method == "picking":
                lines = self.picking_list.mapped("list_line_ids").filtered(lambda l: l.sale_id.id == self.sale_id.id and l.state == "done"
                    and (not l.invoice_id or l.invoice_id.state == "cancel")).ids # filter only sale.order
            elif self.advance_payment_method == "picking_urgent":
                lines = self.picking_list.mapped("list_line_ids").filtered(lambda l: l.sale_id.id == self.sale_id.id and l.state != "cancel"
                    and (not l.invoice_id or l.invoice_id.state == "cancel")).ids
            lines = self.env['picking.lists.line'].browse(lines)
            lines = lines.sorted(lambda l: l.sequence2 or 0)
            self.list_line_ids = lines
            domain = [('id', 'in', lines.ids)]
        else:
            self.list_line_ids = False

        return {'domain': {'list_line_ids': domain}}

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):

        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', [])) # active_ids is sale.order id

        if sale_orders:
            self.sale_id = sale_orders.id

        if self.advance_payment_method == "picking":
            # picking_ids = self.env['picking.lists.line'].search(
            #     [('sale_id', '=', sale_orders.id), ('state', '=', "done"), ('picking_lists.invoice_check', '=', False)])
            picking_ids = self.env['picking.lists.line'].search(
                [('sale_id', '=', sale_orders.id), ('state', '=', "done"),'|',
                    ('invoice_id', '=', False),
                    ('invoice_id.state', '=', 'cancel')])

            list_picking = picking_ids.mapped('picking_lists').ids
        elif self.advance_payment_method == "picking_urgent":
            picking_ids = self.env['picking.lists.line'].search(
                [('picking_lists.is_urgent','=',True),('sale_id', '=', sale_orders.id), ('state', '!=', "cancel"),'|',
                    ('invoice_id', '=', False),
                    ('invoice_id.state', '=', 'cancel')])

            list_picking = picking_ids.mapped('picking_lists').ids
        else:
            # picking_ids = self.env['picking.lists.line'].search(
            #     [('sale_id', '=', sale_orders.id),('picking_lists.invoice_check', '=', False)])

            picking_ids = self.env['picking.lists.line'].search(
                [('sale_id', '=', sale_orders.id)])

            list_picking = picking_ids.mapped('picking_lists').filtered(lambda l: l.is_urgent == True).ids

        return {'domain': {'picking_list': [("id", "in", list_picking)]}}
