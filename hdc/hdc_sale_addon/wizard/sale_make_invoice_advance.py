# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"

    global_discount_price = fields.Float(string = "Global Discount Price",default=lambda self: self._default_global_discount_price(),)
    is_global_discount = fields.Boolean('is global discount',default=lambda self: self._default_is_global_discount(),)

    def _default_global_discount_price(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        global_discount_price = 0
        if sale_orders.global_discount_total:
            global_discount_price = sale_orders.global_discount_total
        return global_discount_price
    
    def _default_is_global_discount(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        is_global_discount = False
        if sale_orders.global_discount:
            is_global_discount = True
        return is_global_discount

    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            sale_orders._create_invoices_global_discount(final = self.deduct_down_payments, global_discount_price = self.global_discount_price)
            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}

        if self.advance_payment_method == 'deduct':
            if not self.product_deduct_id:
                vals = self._prepare_deposit_product()
                self.product_deduct_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('hdc_deduct_down_payments.default_deduct_product_id', self.product_deduct_id.id)
            order_lines = self.deposit_no.invoice_line_ids.mapped('sale_line_ids')
            sale_line_obj = self.env['sale.order.line']
            so_line_values = {
                'name': _('Deduct Down Payment: %s') % (time.strftime('%m %Y'),),
                'price_unit': self.deduct_amount,
                'product_uom_qty': 0,
                'order_id': sale_orders[0].id,
                'product_uom': self.product_deduct_id.uom_id.id,
                'product_id': self.product_deduct_id.id,
                'is_downpayment': True,
                'is_deduct_downpayment': True,
            }
            so_line = sale_line_obj.create(so_line_values)
            self._create_invoice_deduct(so_line)
            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}
        else:
            res = super(SaleAdvancePaymentInv, self).create_invoices()
            return res
