# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import formatLang, get_lang
import re

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.depends('rounding_untax', 'rounding_taxes', 'rounding_total')
    def _amount_all(self):
        super(SaleOrder, self)._amount_all()
        for order in self:
            fiscal_position_tax_id_sale = order.fiscal_position_id.tax_ids.filtered(lambda t: t.tax_dest_id.type_tax_use == 'sale')
            tax_id = fiscal_position_tax_id_sale.tax_dest_id
            amount_untaxed = 0.0
            amount_tax = 0.0
            amount_total = 0.0
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
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_total,
            })
            
        for rec in self:
            if rec.rounding_untax:
                rounding_untax = float(rec.rounding_untax[1:])
                rec.amount_untaxed += rounding_untax if rec.rounding_untax.startswith("+") else -rounding_untax
            if rec.rounding_taxes:
                rounding_taxes = float(rec.rounding_taxes[1:])
                rec.amount_tax += rounding_taxes if rec.rounding_taxes.startswith("+") else -rounding_taxes
            if rec.rounding_total:
                rounding_total = float(rec.rounding_total[1:])
                rec.amount_total += rounding_total if rec.rounding_total.startswith("+") else -rounding_total


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends('triple_discount', 'product_uom_qty', 'price_unit', 'tax_id', 'dis_price','rounding_price')
    def _compute_amount(self):
        for line in self:
            total_dis = 0.0
            price_total = line.price_unit * line.product_uom_qty
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

            price = (line.price_unit * line.product_uom_qty) - total_dis
            
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

            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)
            
            if line.tax_id.price_include:
                price_total = taxes['total_included']
            else:
                price_total = taxes['total_excluded']

            # if line.rounding_price:
            #     try:
            #         rounding_value = float(line.rounding_price[1:])
            #         decimal_precision = self.env['decimal.precision'].precision_get('Sale Rounding')
            #         rounding_pattern = re.compile(r'^[+-]?\d+(\.\d{1,%d})?$' % decimal_precision)
                    
            #         if not rounding_pattern.match(line.rounding_price):
            #             raise ValidationError(_('Invalid Rounding format : +20 or -20 with up to %d decimal places' % decimal_precision))

            #         if line.rounding_price.startswith("+"):
            #             price_total += rounding_value
            #         elif line.rounding_price.startswith("-"):
            #             price_total -= rounding_value
            #         else:
            #             raise ValidationError(_('Invalid Rounding format : +20 or -20'))
            #     except:
            #         raise ValidationError(_('Invalid Rounding format : +20 or -20'))

            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': price_total,
                'price_subtotal': taxes['total_excluded'],
                'dis_price': total_dis,
            })
                        
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])
    
    @api.onchange('product_id')
    def product_id_change(self):
        super(SaleOrderLine, self).product_id_change()
        self.price_unit = self._get_display_price(self.product_id)
        