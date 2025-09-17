# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from datetime import datetime
    
class RecalculateInventoryValuationScheduledLog(models.Model):
    _name = 'recalculate.inventory.valuation.scheduled.log'
    _description = "Recalculate Inventory Valuation Scheduled Log"

    recalculate_date = fields.Datetime(string = "Recalculate Date", readonly=True)
    total_record = fields.Integer(string="Total Records", help="The number of record to recalculate")
    total_product = fields.Integer(string="Total Products", help="The number of product to recalculate")
    range_month = fields.Integer(string="Range of Recalculation (Months)", help="The number of months to recalculate")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self._default_company_id(),index = True,
    )