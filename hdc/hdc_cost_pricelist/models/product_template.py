from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime

class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    @api.model
    def create(self, vals):
        res = super(ProductSupplierinfo, self).create(vals)
        if res.price:
            product_tmpl = self.env['product.template'].browse(res.product_tmpl_id.id)
            cost_pricelist = self.env['cost.pricelist'].search(
                [('product_id', '=', product_tmpl.product_variant_id.id)], limit = 1)
            if cost_pricelist:
                cost_pricelist.po_cost = res.price
                cost_pricelist.current_sale_price = product_tmpl.product_variant_id.lst_price
                cost_pricelist.std_price = product_tmpl.product_variant_id.lst_price
                cost_pricelist.onchange_product_id()
        return res

    def write(self, vals):
        if vals.get('price'):
            product_tmpl = self.env['product.template'].browse(self.product_tmpl_id.id)
            cost_pricelist = self.env['cost.pricelist'].search([('product_id', '=', product_tmpl.product_variant_id.id)], limit=1)
            if cost_pricelist:
                cost_pricelist.po_cost = vals.get('price')
                cost_pricelist.current_sale_price = product_tmpl.product_variant_id.lst_price
                cost_pricelist.std_price = product_tmpl.product_variant_id.lst_price
                cost_pricelist.onchange_product_id()
        res = super(ProductSupplierinfo, self).write(vals)
        return res
    
class ProductTemplate(models.Model):
    _inherit = "product.template"

    source = fields.Selection([('domestic', 'Domestic'), ('inter', 'International')], default = "domestic")
    country_source = fields.Many2one('res.country')
    source_history_ids = fields.One2many(
        comodel_name="product.source.history",
        inverse_name="product_id",
        copy=False
    )

    def write(self, vals):
        if "country_source" in vals:
            for record in self:
                record.source_history_ids.create({
                    'product_id': record.id,
                    'source_from': record.country_source.id,
                    'source_to': vals["country_source"],
                    'last_updated': datetime.now(),
                    'user_id': self.env.user.id
                })
        return super().write(vals)

class ProductSourceHistory(models.Model):
    _name = "product.source.history"
    _description = 'Product Source History'

    product_id = fields.Many2one(comodel_name="product.product")
    source_from = fields.Many2one("res.country")
    source_to = fields.Many2one("res.country")
    last_updated = fields.Datetime(string = 'Last Updated')
    user_id = fields.Many2one(string="Update By", comodel_name="res.users")