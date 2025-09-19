# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_qty = fields.Float(string='Quantity', digits='Purchase Order', required=True)

    gross_unit_price = fields.Float(string = "Gross Unit Price", required = True, digits='Purchase Order',default=0)