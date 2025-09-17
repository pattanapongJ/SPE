# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain = "[('customer', '=', True),('parent_id', '=', False)]")
    
    @api.onchange('partner_id')
    def _get_domain_partner_id_sale_order(self):
        partner_invoice_id = ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id),
                              ('id', 'in', self.partner_id.child_ids.ids), ('type', '=', 'invoice')]
        partner_shipping_id = ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id),
                              ('id', 'in', self.partner_id.child_ids.ids), ('type', '=', 'delivery')]
        res = {}
        domain_partner = [('customer', '=', True),('parent_id', '=', False)]
        res['domain'] = {'partner_invoice_id': partner_invoice_id, 'partner_shipping_id': partner_shipping_id, 'partner_id': domain_partner}
        return res