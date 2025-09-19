# Copyright 2020 Akretion - Mourad EL HADJ MIMOUNE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api,fields, models

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    inter_company_transactions = fields.Boolean(string='Inter Company Transactions')

class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    inter_company_transactions = fields.Boolean(string='Inter Company Transactions')

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id_set_cost(self):
        if self.product_tmpl_id:
            self.pricelist_cost_price = self.product_tmpl_id.cost_group

    @api.onchange("product_id")
    def _onchange_product_id_set_cost(self):
        if self.product_id:
            self.pricelist_cost_price = self.product_id.product_tmpl_id.cost_group


