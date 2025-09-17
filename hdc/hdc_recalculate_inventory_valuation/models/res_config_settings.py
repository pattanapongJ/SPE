# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_inventory_valuation_month = fields.Boolean("Default Recalculate Inventory Valuation", config_parameter='hdc_recalculate_inventory_valuation.use_inventory_valuation_month')
    inventory_valuation_month = fields.Integer(string="Recalculate Inventory Valuation (Months)", readonly=False, config_parameter='hdc_recalculate_inventory_valuation.inventory_valuation_month')

    @api.onchange('inventory_valuation_month')
    def _onchange_inventory_valuation_month(self):
        if self.inventory_valuation_month <= 0 and self.use_inventory_valuation_month == True:
            return {
                'warning': {'title': "Warning", 'message': "Recalculate Inventory Valuation (Months) is required and must be greater than 0."},
            }