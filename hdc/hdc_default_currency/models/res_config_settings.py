# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_sale_currency_res_setting = fields.Many2one('res.currency', string="Default Sale Currency", default_model='res.config.settings', domain="[('rate_type', '=', 'buy'), ('active', '=', True)]", store=True, config_parameter='account_sale_currency_res_setting')

    account_purchase_currency_res_setting = fields.Many2one('res.currency', string="Default Purchase Currency", default_model='res.config.settings', domain="[('rate_type', '=', 'sell'), ('active', '=', True)]", store=True, config_parameter='account_purchase_currency_res_setting')