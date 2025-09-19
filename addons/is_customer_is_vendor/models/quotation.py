# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Quotations(models.Model):
    _inherit = 'quotation.order'

    partner_id = fields.Many2one('res.partner', string = 'Customer', readonly = True,
        states = {'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required = True,
        change_default = True, index = True, tracking = 1,
        domain = "[('customer','=', True)]")
    
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Account', readonly=True, required=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="[('customer','=', True)]", )

    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="[('customer','=', True)]", )