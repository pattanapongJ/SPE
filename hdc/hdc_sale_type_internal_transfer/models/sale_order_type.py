# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class SaleOrderTypology(models.Model):
    _inherit = "sale.order.type"
    
    is_retail = fields.Boolean(string='Is Retail')
    is_booth = fields.Boolean(string='Is Booth & Consignment')
    is_no_spe_invoice = fields.Boolean(string='No SPE Invoice')
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type',)
    is_online = fields.Boolean(string='Is Online')