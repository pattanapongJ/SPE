# -*- coding: utf-8 -*-
from odoo import api, models, fields, _

class SaleOrderTypology(models.Model):
    _inherit = "sale.order.type"
    
    is_dewalt = fields.Boolean(string='Is Dewalt')