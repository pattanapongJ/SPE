# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import re

class Quotations(models.Model):
    _inherit = 'quotation.order'
    _description = "Quotations Order"

    billing_place_id = fields.Many2one(comodel_name='account.billing.place', string="Billing Place")
    billing_terms_id = fields.Many2one(comodel_name='account.billing.terms', string="Billing Terms")
    payment_period_id = fields.Many2one(comodel_name='account.payment.period', string="Payment Period")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):

        if self.partner_id.billing_period_id:
            self.billing_period_id = self.partner_id.billing_period_id.id
        if self.partner_id.billing_route_id:
            self.billing_route_id = self.partner_id.billing_route_id.id
        if self.partner_id.billing_place_id:
            self.billing_place_id = self.partner_id.billing_place_id.id
        if self.partner_id.billing_terms_id:
            self.billing_terms_id = self.partner_id.billing_terms_id.id
        if self.partner_id.payment_period_id:
            self.payment_period_id = self.partner_id.payment_period_id.id

    def create_sale_order(self):
        quotation_line = []
        for line in self.quotation_line:
            quotation_line.append((0,0, {
                        'name': line.name,
                        'price_unit': line.price_unit,
                        'tax_id': line.tax_id.ids,
                        'product_id': line.product_id.id,
                        'product_template_id': line.product_template_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'product_uom_category_id': line.product_uom_category_id.id,
                        'product_no_variant_attribute_value_ids': line.product_no_variant_attribute_value_ids.ids,
                        'display_type': line.display_type,
                        'triple_discount': line.triple_discount,
                        'rounding_price': line.rounding_price,
                        'is_global_discount': line.is_global_discount
                        }))
        quotation = {
            'order_line': quotation_line,
            'quotation_id': self.id,
            'default_product_global_discount': self.default_product_global_discount.id,
            'origin': self.origin,
            'client_order_ref': self.client_order_ref,
            'reference': self.reference,
            'date_order': self.date_order,
            'validity_date': self.validity_date,
            'require_signature': self.require_signature,
            'require_payment': self.require_payment,
            'partner_id': self.partner_id.id,
            'partner_invoice_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'pricelist_id': self.pricelist_id.id,
            'currency_id': self.currency_id.id,
            'note': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
            'company_id': self.company_id.id,
            'team_id': self.team_id.id,
            'signature': self.signature,
            'signed_by': self.signed_by,
            'signed_on': self.signed_on,
            'commitment_date': self.commitment_date,
            'show_update_pricelist': self.show_update_pricelist,
            'customer_po': self.customer_po,
            'total_discount': self.total_discount,
            'global_discount': self.global_discount,
            'global_discount_update': self.global_discount_update,
            'priority': self.priority,
            'delivery_time': self.delivery_time.id,
            'delivery_terms': self.delivery_terms.id,
            'offer_validation': self.offer_validation.id,
            'sale_spec': self.sale_spec.id,
            'user_sale_agreement': self.user_sale_agreement.id,
            'user_id': self.user_id.id,
            'sale_manager_id': self.sale_manager_id.id,
            'modify_type_txt': self.modify_type_txt,
            'plan_home': self.plan_home,
            'requested_ship_date': self.requested_ship_date,
            'requested_receipt_date': self.requested_receipt_date,
            'delivery_trl': self.delivery_trl.id,
            'customer_contact_date': self.customer_contact_date,
            'delivery_company': self.delivery_company.id,
            'remark': self.remark,
            'type_id': self.type_id.id,
            'billing_period_id': self.billing_period_id.id,
            'billing_route_id': self.billing_route_id.id,
            'billing_place_id': self.billing_place_id.id,
            'billing_terms_id': self.billing_terms_id.id,
            'payment_period_id': self.payment_period_id.id,
            'blanket_order_id': self.blanket_order_id.id,
            'contact_person': self.contact_person.id,
            'warehouse_id': self.warehouse_id.id,
            }
        sale_id = self.env['sale.order'].create(quotation)
        action = {
            'name': 'Sales Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_id.id,
            'view_mode': 'form',
            }
        return action