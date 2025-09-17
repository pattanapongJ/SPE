# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"     

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    shipping_cost = fields.Float(string="Shipping Cost")
    sale_uom_map_ids = fields.Many2many(related="product_id.sale_uom_map_ids")

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['shipping_cost'] = self.shipping_cost
        return res

    @api.onchange('product_id', 'product_uom_qty', 'product_uom')
    def _onchange_update_pricelist(self):        
        self.pricelist_line_shipping_cost()

    # @api.onchange('product_uom_ids') # ปิดการทำงาน เพราะว่าจะใช้ hdc_prod_convert_uom
    # def _onchange_product_uom_ids(self):     
    #     domain_uom = [("id", "in", self.product_uom_ids.ids)]    
    #     return {'domain': {'product_uom': domain_uom}}

    def pricelist_line_shipping_cost(self):
        self.find_and_update_pricelist(pricelist_val=self.order_id.pricelist_id)

    def find_and_update_pricelist(self, pricelist_val):

        if self.product_id.type != 'service':

            product_tmpl = self.product_id.product_tmpl_id

            product_uom_val = self.product_uom.id if self.product_uom.id else product_tmpl.uom_id.id
                
            find_pricelist_tmpl = pricelist_val.item_ids.filtered(lambda pl: pl.applied_on == '1_product' and pl.product_tmpl_id.id == product_tmpl.id and pl.product_uom_id.id == product_uom_val)

            if find_pricelist_tmpl:
                for tmpl in find_pricelist_tmpl:                    

                    self.price_unit = tmpl.fixed_price # Price Unit
                    self.triple_discount = tmpl.triple_discount # Discount
                    self.shipping_cost = tmpl.shipping_cost # Shipping
                    self.discount_pricelist =  tmpl.dis_price # Unit Price List

            else:
                self.price_unit = product_tmpl.lst_price # Price Unit
                self.triple_discount = 0 # Discount
                self.shipping_cost = 0 # Shipping
                self.discount_pricelist = 0 # Unit Price List

    # ไม่รู้เลยว่ามี code ตรงส่วนไหนไปแก้ไขการทำงานของ unit price อีก เลยมาตรวจสอบอีกรอบที่ discount_pricelist
    @api.onchange('discount_pricelist')
    def _onchange_discount_pricelist(self):
        if self.discount_pricelist > 0: # have value from pricelist -> stamp again
            pricelist_vals = self.order_id.pricelist_id
            search_pricelist_vals = pricelist_vals.item_ids.filtered(lambda pl: pl.applied_on == '1_product' and pl.product_tmpl_id.id == self.product_id.product_tmpl_id.id and pl.product_uom_id.id == self.product_uom.id)

            if search_pricelist_vals:
                for tmpl in search_pricelist_vals:
                    self.price_unit = tmpl.fixed_price # Price Unit





