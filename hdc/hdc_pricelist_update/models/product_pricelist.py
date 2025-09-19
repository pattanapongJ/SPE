# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # ฟิลด์สำหรับการ import ไฟล์
    import_pricelist = fields.Binary(string="Import File")
    file_name_import = fields.Char(string="File Name")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # ฟิลด์สำหรับการ import ไฟล์
    import_pricelist = fields.Binary(string="Import File")
    file_name_import = fields.Char(string="File Name")


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    amount_pricelist_update = fields.Integer(
        sting="Amount Pricelist Update", compute="_amount_pricelist_update"
    )

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product', ondelete='cascade', check_company=False,
        help="Specify a template if this rule only applies to one product template. Keep empty otherwise.")
    product_id = fields.Many2one(
        'product.product', 'Product Variant', ondelete='cascade', check_company=False,
        help="Specify a product if this rule only applies to one product. Keep empty otherwise.")

    def _amount_pricelist_update(self):
        for item in self:
            amount_pricelist = self.env["pricelist.update"].search_count(
                [(("item_ids_line.product_tmpl_id", "=", item.product_tmpl_id.id))]
            )
            item.amount_pricelist_update = amount_pricelist

    def action_button_method(self):
        self.ensure_one()
        product_tmpl_id = self.product_tmpl_id.id
        product_update_ids = self.env["pricelist.update"].search(
            [(("item_ids_line.product_tmpl_id", "=", product_tmpl_id))]
        )
        return {
            "name": _("Price Update"),
            "view_mode": "tree,form",
            "res_model": "pricelist.update",
            "domain": [("id", "in", product_update_ids.ids)],
            "type": "ir.actions.act_window",
            "target": "current",
        }
