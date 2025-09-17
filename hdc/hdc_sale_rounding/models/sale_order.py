# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    rounding_untax = fields.Char(string='Rounding Untaxed Amount')
    rounding_taxes = fields.Char(string='Rounding Taxes')
    rounding_total = fields.Char(string='Rounding Total')

    def action_rounding_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Total Rounding',
            'view_mode': 'form',
            'res_model': 'wizard.sale.change.total',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_rounding_untax': self.rounding_untax,
                'default_rounding_taxes': self.rounding_taxes,
                'default_rounding_total': self.rounding_total,
            },
        }
    @api.depends('rounding_untax', 'rounding_taxes', 'rounding_total')
    def _amount_all(self):
        super(SaleOrder, self)._amount_all()
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

    rounding_price = fields.Char('Rounding')
    @api.depends('triple_discount', 'product_uom_qty', 'price_unit', 'tax_id', 'dis_price','rounding_price')
    def _compute_amount(self):
        for line in self:
            total_dis = 0.0
            price_total = line.price_unit
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

            price = (line.price_unit - total_dis) * line.product_uom_qty
            
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
            
            price_total = taxes['total_included']
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': price_total,
                'price_subtotal': taxes['total_excluded'],
            })
                        
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])