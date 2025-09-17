# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Quotations(models.Model):
    _inherit = 'quotation.order'

    def open_wizard_create_sale_order(self):
        line_ids = []
        if self.quotation_line:
            for line in self.quotation_line:
                if line.is_global_discount == False:
                    line_ids.append((0, 0, {
                        'quotation_line': line.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'price_unit': line.price_unit,
                        'display_type': line.display_type,
                        'name': line.name,
                        "external_customer": line.external_customer.id if line.external_customer else False,
                        "external_item": line.external_item,
                        "barcode_customer": line.barcode_customer,
                        "barcode_modern_trade": line.barcode_modern_trade,
                        "description_customer": line.description_customer,
                        "modify_type_txt": line.modify_type_txt,
                        "plan_home": line.plan_home,
                        "room": line.room,
                        "shipping_cost": line.shipping_cost,
                        "discount_pricelist": line.discount_pricelist
                        }))
                    
        wizard = self.env["wizard.create.sale.order"].create({
            "quotation_id": self.id,
            "order_line": line_ids
            })
        
        action = {
            'name': 'Create Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.create.sale.order',
            'res_id': wizard.id,
            'view_mode': 'form',
            "target": "new",
            }
        return action


class QuotationLine(models.Model):
    _inherit = 'quotation.order.line'

    discount_pricelist = fields.Float('Unit Price Pricelist', readonly=True)
    shipping_cost = fields.Float(string="Shipping Cost", readonly=True)
    sale_uom_map_ids = fields.Many2many(related="product_id.sale_uom_map_ids")

    @api.onchange('product_id', 'product_uom')
    def _onchange_update_pricelist(self):        
        self.pricelist_line_shipping_cost()

    def pricelist_line_shipping_cost(self):
        self.find_and_update_pricelist(pricelist_val=self.quotation_id.pricelist_id)

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