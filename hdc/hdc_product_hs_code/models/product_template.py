# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hs_code_id = fields.Many2one('product.hs.code', string="HS Code")