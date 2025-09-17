# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    factory_cost = fields.Float(string='Factory Cost',)
    mrp_margin = fields.Float(string='Margin (%)',)
    factory_sale_price = fields.Float(string='Factory Sale Price',)


