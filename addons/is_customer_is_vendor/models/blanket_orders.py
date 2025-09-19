# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    partner_id = fields.Many2one("res.partner",string="Customer",readonly=True,states={"draft": [("readonly", False)]},
                                 domain = "[('customer', '=', True)]")
    
    @api.onchange('partner_id')
    def _get_domain_partner_id_sale_order(self):
        partner_invoice_id = [('customer', '=', True)]
        partner_shipping_id = [('customer', '=', True)]
        res = {}
        domain_partner = [('customer', '=', True)]
        res['domain'] = {'partner_invoice_id': partner_invoice_id, 'partner_shipping_id': partner_shipping_id, 'partner_id': domain_partner}
        return res
    
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Account',required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id),('parent_id','=',partner_id), ('type', '=', 'invoice'), ('customer', '=', True)]")
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address', required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id),('parent_id','=',partner_id), ('type', '=', 'delivery'), ('customer', '=', True)]")
    