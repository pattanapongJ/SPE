# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode
import re
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang


class SaleOrder(models.Model):
    _inherit = "sale.order"

    discount_percen = fields.Float("ส่วนลด%", tracking=True)
    discount_price = fields.Float("ส่วนลด", tracking=True)
    discount_total_price = fields.Float("ส่วนลดจำนวนเงิน", tracking=True, compute='_amount_all')
    discount = fields.Float("ส่วนลดรวม", tracking=True, compute='_compute_amount_discount')

    @api.depends('order_line.price_total', 'discount', 'discount_price', 'discount_percen','global_discount','global_discount_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        res = super(SaleOrder, self)._amount_all()
        total_dis_price = 0.0
        for line in self:
            if line.discount_percen:
                total_dis_price += ((line.amount - line.discount) * line.discount_percen) / 100
            if line.discount_price:
                total_dis_price += line.discount_price

        for order in self:
            amount_untaxed = amount_tax = amount_untaxed_total = 0.0
            amount_untaxed_total_global = 0.0
            for line in order.order_line:

                amount_untaxed += line.price_total
                amount_untaxed_total += (line.price_unit * line.product_uom_qty)
                amount_tax += line.price_tax

                #ส่วนลดต่อ
                amount_untaxed_total_global += line.price_subtotal

            amount_total = amount_untaxed

            # amount_vat = amount_untaxed_total_global
            # amount_vat_total_global = (amount_untaxed_total_global - order.global_discount_total) * 0.07

            # กรณีที่มีการทำส่วนลดต่อ
            # สูตรทั่วไป vat = untaxed amount * vat(7%)
            # สูตรกรณีมีส่วนลด Global discount บาท = untaxed amount -Global discount * vat(7%)
            if order.global_discount_total: 
                order.update({
                'amount_untaxed': amount_untaxed_total_global,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed_total_global + amount_tax,
                'discount_total_price': total_dis_price,
            })

            # กรณีไม่ใช่ส่วนลดต่อ
            else:
                order.update({
                    'amount_untaxed': amount_untaxed_total_global,
                    'amount_tax': amount_tax,
                    'amount_total': amount_untaxed_total_global + amount_tax,
                    'discount_total_price': total_dis_price,
                })

        return res
    
    @api.depends('order_line', 'discount')
    def _compute_amount_discount(self):
        total_dis_price = 0.0
        for line in self:
            for dis in line.order_line:
                total_dis_price += dis.dis_price
            line.update({
                'discount': total_dis_price
            })

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    triple_discount = fields.Char('Discount')
    discount_pricelist = fields.Float('Unit Price Pricelist', readonly=True)
    dis_price = fields.Float('Discount price', compute='_compute_amount')

    @api.onchange('product_id', 'product_uom_qty')
    def triple_discount_pricelist(self):
        check_product = self.env["product.pricelist.item"].search([("pricelist_id", "=", self.order_id.pricelist_id.id),
            ("product_tmpl_id", "=", self.product_id.product_tmpl_id.id),
            ("min_quantity", "<=", self.product_uom_qty)], order='min_quantity desc', limit=1)
        if check_product:
            if check_product.triple_discount:
                self.triple_discount = check_product.triple_discount
                self.discount_pricelist = check_product.dis_price
            else:
                self.triple_discount = ""
                self.discount_pricelist = 0.0
    
    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = product.currency_id
        
        
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
                product_currency = product.cost_currency_id
            elif pricelist_item.base == 'cost_bernuly':
                field_name = 'standard_price'
                product_currency = product.cost_currency_id
            # if pricelist_item.base == 'cost_bernuly':
            #     field_name = 'cost_bernuly'
            #     product_currency = product.cost_currency_id
            elif pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id or self.env.company, self.order_id.date_order or fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id

    @api.depends('triple_discount', 'product_uom_qty', 'price_unit', 'tax_id', 'dis_price')
    def _compute_amount(self):
        # ไม่ได้ใช้
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
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, 1,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'dis_price': total_dis,
            })
                        
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['triple_discount'] = self.triple_discount
        res['price_subtotal'] = self.price_subtotal
        return res

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    triple_discount = fields.Char('Discount')
    dis_price = fields.Float('Price', compute = '_compute_amount_triple_discount')

    @api.depends('triple_discount', 'fixed_price')
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
            line.dis_price = line.fixed_price - total_dis



    
