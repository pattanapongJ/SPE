from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.exceptions import UserError
from odoo.exceptions import Warning


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _description = "Product Template"
    
    bns_code = fields.Char(string="BNS CODE")
    

class ProductProduct(models.Model):
    _inherit = "product.product"
    _description = "Product"

    bns_code = fields.Char(string="BNS CODE", compute="_compute_bns_code")

    @api.depends('product_tmpl_id')
    def _compute_bns_code(self):
        for product in self:
            bns_code_check = self.env["product.template"].search([('product_variant_ids', 'in', product.id)])
            if bns_code_check:
                product.bns_code = bns_code_check.bns_code
    

    # bns_code = fields.Char(string="BNS CODE" , compute="_default_bns_code")
    

    # def _default_bns_code(self):
    #     bns_code_check = self.env["product.template"].search(
    #         [('product_variant_ids', 'in', self.id)]
    #         )
    #         print(self.product_tmpl_id , "product_tmpl_idproduct_tmpl_idproduct_tmpl_idproduct_tmpl_id")
    #     if bns_code_check:
    #         self.bns_code = bns_code_check.bns_code





