# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import formatLang, get_lang

class SaleOrder(models.Model):
    _inherit = "sale.order"


    currency_id = fields.Many2one(related='pricelist_id.currency_id', depends=["pricelist_id"], store=True)

    # currency_id = fields.Many2one('res.currency', store = True, domain="[('rate_type', '=', 'buy'), ('active', '=', True)]", default=lambda self: self._default_currency())

    @api.model
    def _default_currency(self):
        currency_id = self.env['ir.config_parameter'].sudo().get_param('account_sale_currency_res_setting')
        return int(currency_id)