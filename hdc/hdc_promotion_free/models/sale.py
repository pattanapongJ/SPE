from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from odoo.tools import float_is_zero
from odoo import api, fields, models, SUPERUSER_ID, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sales Order Line'
    
    free_product = fields.Boolean(string='Free Product')
    free_product_check = fields.Boolean(related='product_id.free_product',string='Free Product')
    
    @api.onchange('free_product','product_uom_qty')
    def _onchange_free_product_fields(self):
        if self.free_product is True:
            self.price_unit = 0.0
            self.triple_discount = False
        else:
            if not self.price_unit:
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

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if self.free_product is True:
            self.price_unit = 0.0
            self.triple_discount = False
            return 
        res = super(SaleOrderLine, self).product_uom_change()
        
        return res
    
    def write(self, values):
        # ตรวจสอบว่ามีการตั้งค่า free_product เป็น True หรือไม่
        if 'free_product' in values and values['free_product']:
            if 'price_unit' not in values or values['price_unit'] != 0.0:
                values['price_unit'] = 0.0

        res = super(SaleOrderLine, self).write(values)

        # ตรวจสอบอีกครั้งหลังจากการบันทึก (กรณีที่ free_product ถูกตั้งค่าแล้ว)
        free_lines = self.filtered(lambda line: line.free_product and line.price_unit != 0.0)
        if free_lines:
            free_lines.with_context(skip_recursion=True).write({'price_unit': 0.0})

        return res


class QuotationLine(models.Model):
    _inherit = 'quotation.order.line'
    
    free_product = fields.Boolean(string='Free Product')
    free_product_check = fields.Boolean(related='product_id.free_product',string='Free Product')
    
    @api.onchange('free_product','product_uom_qty')
    def _onchange_free_product_fields(self):
        if self.free_product is True:
            self.price_unit = 0.0
            self.triple_discount = False
        else:
            # if not self.price_unit:
                product = self.product_id.with_context(
                    lang=self.quotation_id.partner_id.lang,
                    partner=self.quotation_id.partner_id,
                    quantity=self.product_uom_qty,
                    date=self.quotation_id.date_order,
                    pricelist=self.quotation_id.pricelist_id.id,
                    uom=self.product_uom.id,
                    fiscal_position=self.env.context.get('fiscal_position')
                )
                self.price_unit = self._get_display_price(product)
                    

    # @api.onchange('product_uom', 'product_uom_qty')
    # def product_id_change(self):
    #     res = super(QuotationLine, self).product_id_change()
    #     if self.free_product is True:
    #         self.price_unit = 0.0
    #         self.triple_discount = False
    #         return 
        
    #     return res
    
    def write(self, values):
        # ตรวจสอบว่ามีการตั้งค่า free_product เป็น True หรือไม่
        if 'free_product' in values and values['free_product']:
            if 'price_unit' not in values or values['price_unit'] != 0.0:
                values['price_unit'] = 0.0

        res = super(QuotationLine, self).write(values)

        # ตรวจสอบอีกครั้งหลังจากการบันทึก (กรณีที่ free_product ถูกตั้งค่าแล้ว)
        free_lines = self.filtered(lambda line: line.free_product and line.price_unit != 0.0)
        if free_lines:
            free_lines.with_context(skip_recursion=True).write({'price_unit': 0.0})

        return res
    
    
class BlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"
    
    free_product = fields.Boolean(string='Free Product')
    free_product_check = fields.Boolean(related='product_id.free_product',string='Free Product')
    
    @api.onchange('free_product','original_uom_qty')
    def _onchange_free_product_fields(self):
        if self.free_product:
            self.price_unit = 0.0
            self.triple_discount = False
        else:
            if not self.price_unit:
                product = self.product_id.with_context(
                    lang=self.order_id.partner_id.lang,
                    partner=self.order_id.partner_id,
                    quantity=self.original_uom_qty,
                    date=fields.Date.today(),
                    pricelist=self.order_id.pricelist_id.id,
                    uom=self.product_uom.id,
                    fiscal_position=self.env.context.get('fiscal_position')
                )
                self.price_unit = self._get_display_price(product)

    @api.onchange("product_id", "original_uom_qty")
    def onchange_product(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        if self.product_id:
            name = self.product_id.name
            if not self.product_uom:
                self.product_uom = self.product_id.uom_id.id
            # if self.order_id.partner_id and self.free_product is False and float_is_zero(
            #     self.price_unit, precision_digits=precision
            # ):
                # self.price_unit = self._get_display_price(self.product_id)
            if self.order_id.partner_id and self.free_product is False :
                product = self.product_id.with_context(
                    lang=self.order_id.partner_id.lang,
                    partner=self.order_id.partner_id,
                    quantity=self.original_uom_qty,
                    date=fields.Date.today(),
                    pricelist=self.order_id.pricelist_id.id,
                    uom=self.product_uom.id,
                    fiscal_position=self.env.context.get('fiscal_position')
                )
                self.price_unit = self._get_display_price(product)
            # if self.product_id.code:
            #     name = "[{}] {}".format(name, self.product_id.code)
            if self.product_id.description_sale:
                name = self.product_id.description_sale
            self.name = name

            fpos = self.order_id.fiscal_position_id or self.order_id.fiscal_position_id.get_fiscal_position(self.order_id.partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = self.product_id.taxes_id.filtered(lambda t: t.company_id == self.env.company)
            self.taxes_id = fpos.map_tax(taxes, self.product_id, self.order_id.partner_shipping_id)