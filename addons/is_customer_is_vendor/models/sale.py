# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain = "[('customer', '=', True)]")
    
    @api.onchange('partner_id')
    def _get_domain_partner_id_sale_order(self):
        partner_invoice_id = [('customer', '=', True)]
        partner_shipping_id = [('customer', '=', True)]
        res = {}
        domain_partner = [('customer', '=', True)]
        res['domain'] = {'partner_invoice_id': partner_invoice_id, 'partner_shipping_id': partner_shipping_id, 'partner_id': domain_partner}
        return res