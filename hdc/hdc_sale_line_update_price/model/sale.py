# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import formatLang, get_lang

class SalesOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):

        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self._get_display_price(product)
            # เอาเช็คค่า0ออก ให้มันเปลี่ยนไปก่อน
            # if self.price_unit == 0:
            #     self.price_unit = product._get_tax_included_unit_price(
            #         self.company_id,
            #         self.order_id.currency_id,
            #         self.order_id.date_order,
            #         'sale',
            #         fiscal_position=self.order_id.fiscal_position_id,
            #         product_price_unit=self._get_display_price(product),
            #         product_currency=self.order_id.currency_id
            #     )