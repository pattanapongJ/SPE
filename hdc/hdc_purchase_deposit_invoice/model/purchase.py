from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby
import re
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'qty_received', 'product_uom_qty', 'order_id.state')
    def _compute_qty_invoiced(self):
        for line in self:
            # compute qty_invoiced
            qty = 0.0
            for inv_line in line.invoice_lines:
                if inv_line.move_id.state not in ['cancel']:
                    if inv_line.move_id.move_type == 'in_invoice':
                        qty += inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
                    elif inv_line.move_id.move_type == 'in_refund':
                        qty -= inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
            line.qty_invoiced = qty

            # compute qty_to_invoice
            if line.order_id.state in ['purchase', 'done']:
                if line.product_id.purchase_method == 'purchase':
                    line.qty_to_invoice = line.product_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_received - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

            if line.qty_invoiced > 0:
                for inv_line in line.invoice_lines:
                    if inv_line.move_id.state == 'posted':
                        deposit_product = self.env['ir.config_parameter'].sudo().get_param('purchase_deposit.default_purchase_deposit_product_id')
                        if inv_line.product_id.id == int(deposit_product):
                            deposit_price = inv_line.price_unit
                            line.gross_unit_price = deposit_price

    def _prepare_account_move_line(self, move=False):

        result = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)
        if self.is_deposit:
            result['price_unit'] = self.gross_unit_price
            result.update({
                'price_unit': self.gross_unit_price
            })
        result.update({
                'gross_unit_price': self.gross_unit_price
            })
        return result