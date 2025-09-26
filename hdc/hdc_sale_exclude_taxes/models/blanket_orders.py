# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from collections import defaultdict
import re

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    @api.depends('line_ids.price_total','rounding_untax', 'rounding_taxes', 'rounding_total','global_discount')
    def _compute_amount_all(self):
        for order in self:
            fiscal_position_tax_id_sale = order.fiscal_position_id.tax_ids.filtered(lambda t: t.tax_dest_id.type_tax_use == 'sale')
            tax_id = fiscal_position_tax_id_sale.tax_dest_id
            amount_untaxed = 0.0
            amount_tax = 0.0
            amount_total = 0.0
            order._compute_amount_before_discount()
            order._compute_total_discount()
            if tax_id.price_include:
                tax_rate_amount = tax_id.amount
                amount_total = order.amount_before_discount - order.total_discount_amount_new
                amount_tax = (amount_total * tax_rate_amount) / (100+tax_rate_amount)
                amount_untaxed = amount_total - amount_tax
            else:
                tax_rate_amount = tax_id.amount
                amount_untaxed = order.amount_before_discount - order.total_discount_amount_new
                amount_tax = amount_untaxed * (tax_rate_amount/100)
                amount_total = amount_untaxed + amount_tax

            if order.rounding_untax:
                rounding_untax = float(order.rounding_untax[1:])
                amount_untaxed += rounding_untax if order.rounding_untax.startswith("+") else -rounding_untax
            if order.rounding_taxes:
                rounding_taxes = float(order.rounding_taxes[1:])
                amount_tax += rounding_taxes if order.rounding_taxes.startswith("+") else -rounding_taxes
            if order.rounding_total:
                rounding_total = float(order.rounding_total[1:])
                amount_total += rounding_total if order.rounding_total.startswith("+") else -rounding_total
                
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_total,
            })

    

class BlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    @api.depends('triple_discount', 'original_uom_qty', 'price_unit', 'taxes_id', 'dis_price', 'rounding_price')
    def _compute_amount(self):
        for line in self:
            total_dis = 0.0
            price_total = line.price_unit * line.original_uom_qty
            if line.triple_discount:
                try:
                    discounts = line.triple_discount.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                    for discount in discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for discount in discounts:
                        if discount.endswith("%"):
                            dis_percen = discount.replace("%", "")
                            total_percen = ((price_total) * float(dis_percen)) / 100
                            price_total -= total_percen
                            total_dis += total_percen
                        else:
                            total_baht = float(discount) 
                            price_total -= total_baht
                            total_dis += total_baht
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))

            price = (line.price_unit * line.original_uom_qty) - total_dis
            
            if line.rounding_price:
                try:
                    rounding_value = float(line.rounding_price[1:])
                    decimal_precision = self.env['decimal.precision'].precision_get('Sale Rounding')
                    rounding_pattern = re.compile(r'^[+-]?\d+(\.\d{1,%d})?$' % decimal_precision)
                    
                    if not rounding_pattern.match(line.rounding_price):
                        raise ValidationError(_('Invalid Rounding format : +20 or -20 with up to %d decimal places' % decimal_precision))

                    if line.rounding_price.startswith("+"):
                        price += rounding_value
                    elif line.rounding_price.startswith("-"):
                        price -= rounding_value
                    else:
                        raise ValidationError(_('Invalid Rounding format : +20 or -20'))
                except:
                    raise ValidationError(_('Invalid Rounding format : +20 or -20'))

            taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)
            
            if line.taxes_id.price_include:
                price_total = taxes['total_included']
            else:
                price_total = taxes['total_excluded']

            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': price_total,
                'price_subtotal': taxes['total_excluded'],
                'dis_price': total_dis,
            })
                        
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.taxes_id.invalidate_cache(['invoice_repartition_line_ids'], [line.taxes_id.id])

    @api.onchange('product_id')
    def product_id_change(self):
        self.price_unit = self._get_display_price(self.product_id)
    