# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ext_product_vendor_available = fields.Integer(string="External Items Vendor", compute='_compute_multi_ext_vendor_product')

    def _compute_multi_ext_vendor_product(self):
        for line in self:
            multi_ext_product_count = line.env['multi.external.vendor'].search_count([('product_tmpl_id', '=',line.id)]) 
            line.update({   
                 'ext_product_vendor_available': multi_ext_product_count,
                })           

    def action_view_multi_ext_product_detail(self):
        multi_ext_product_ids = self.env['multi.external.vendor'].search([('product_tmpl_id', '=',self.id)])
        context = {'default_product_tmpl_id':self.id}
        return {
            "name": _("รายละเอียด"),
            "view_mode": "tree,form",
            "res_model": "multi.external.vendor",
            "type": "ir.actions.act_window",
            "domain": [("id", "in", multi_ext_product_ids.ids)] or [],
            'context': context,              
            }