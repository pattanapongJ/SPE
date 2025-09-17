# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import re


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    shipping_cost = fields.Float(string="Shipping Cost", default=0.00)

    dis_price = fields.Float('Price', compute = '_compute_amount_triple_discount')
    remark = fields.Text(string="Remark")

    @api.depends('triple_discount', 'fixed_price', "shipping_cost")
    def _compute_amount_triple_discount(self):
        for line in self:
            total_dis = 0.0
            price_total = line.fixed_price
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
                            total_percen = ((price_total)*float(dis_percen))/100
                            price_total -= total_percen
                            total_dis += total_percen
                        else:
                            total_baht = float(discount)
                            price_total -= total_baht
                            total_dis += total_baht
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))
                
            line.dis_price = (line.fixed_price - total_dis) + line.shipping_cost

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def get_product_price_rule(self, product, quantity, partner, date=False, uom_id=False):

        if not product:
            raise ValidationError(
                    _(
                        "กรุณาเลือก Customer ก่อนเลือก Product"
                    )
                )

        result = super(ProductPricelist, self).get_product_price_rule(product, quantity, partner, date=date, uom_id=uom_id)

        return result