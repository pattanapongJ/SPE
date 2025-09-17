# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang
from collections import defaultdict

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    promotion_discount = fields.Float(string="Discount Promotion", digits='Product Price')

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        res = {}
        price_total = (price_unit * quantity) - self.promotion_discount
        if self.triple_discount:
            price_total = self._apply_triple_discount(price_total,quantity)
        subtotal = price_total
        if self.rounding_price:
            rounding_value = float(self.rounding_price[1:])
            if self.rounding_price.startswith("+"):
                subtotal += rounding_value
            elif self.rounding_price.startswith("-"):
                subtotal -= rounding_value
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(subtotal,
                quantity=1, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res
    
    @api.depends('triple_discount','quantity','price_unit','promotion_discount')
    def _compute_amount(self):
        for line in self:
            total_dis = 0.0
            price_total = (line.price_unit * line.quantity) - line.promotion_discount
            if line.triple_discount:
                try:
                    discounts = line.triple_discount.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                    for discount in discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for dis in discounts:
                        if dis.endswith("%"):
                            dis_percen = dis.replace("%", "")
                            total_percen = ((price_total) * float(dis_percen)) / 100
                            price_total -= total_percen
                            total_dis += total_percen
                        else:
                            total_baht = float(dis) * line.quantity
                            price_total -= total_baht
                            total_dis += total_baht
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))
            if line.promotion_discount and total_dis == 0.0:
                total_dis = line.promotion_discount
            line.dis_price = total_dis
            line.update(line._get_price_total_and_subtotal())