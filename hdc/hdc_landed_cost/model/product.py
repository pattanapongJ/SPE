# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    landed_cost_type = fields.Selection(
        [('do', 'DO'),
         ('shipping','ค่า Shipping'),
         ('insurance','ค่าประกัน')], 
        string="Landed Cost Type", default="do"
   )