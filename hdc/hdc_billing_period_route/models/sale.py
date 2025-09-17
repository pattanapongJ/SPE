# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    billing_period_id = fields.Many2one(comodel_name='account.billing.period', string="Billing Period")

    billing_route_id = fields.Many2one(comodel_name='account.billing.route', string="Billing Route")

    customer_po = fields.Char(string="",copy=False)

    expire_date = fields.Date(string="Expire Date PO")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):

        if self.partner_id.billing_period_id or self.partner_id.billing_route_id:
            self.billing_period_id = self.partner_id.billing_period_id.id
            self.billing_route_id = self.partner_id.billing_route_id.id

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.billing_period_id:
            res["billing_period_id"] = self.billing_period_id.id
        if self.billing_route_id:
            res["billing_route_id"] = self.billing_route_id.id
        return res
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            form_view = self.env.ref('hdc_billing_period_route.hdc_billing_route_view_order_form_inherit')
            form_view_pay = self.env.ref('hdc_billing_period_route.sale_payment_method_view_order_form_inherit')
            arch_tree = etree.fromstring(form_view.arch)
            arch_tree_pay = etree.fromstring(form_view_pay.arch)
            if not self.env.user.has_group('sales_team.group_sale_manager'):
                for node in arch_tree_pay.xpath("//field[@name='payment_method_id']"):
                    node.set('readonly', '1')
                for node1 in arch_tree_pay.xpath("//field[@name='payment_term_id']"):
                    node1.set('readonly', '1')
                for node2 in arch_tree.xpath("//field[@name='billing_period_id']"):
                    node2.set('readonly', '1')
            else:
                for node in arch_tree_pay.xpath("//field[@name='payment_method_id']"):
                    node.set('readonly', '0')
                for node1 in arch_tree_pay.xpath("//field[@name='payment_term_id']"):
                    node1.set('readonly', '0')
                for node2 in arch_tree.xpath("//field[@name='billing_period_id']"):
                    node2.set('readonly', '0')
            form_view.sudo().write({'arch': etree.tostring(arch_tree, encoding='unicode')})
            form_view_pay.sudo().write({'arch': etree.tostring(arch_tree_pay, encoding='unicode')})
        return res


    @api.onchange("partner_id", "team_id")
    def onchange_credit_limit_partner_id_team_id(self):
        customer_credit_id = self.env["customer.credit.limit"].search([('partner_id', '=', self.partner_id.id)])
        if customer_credit_id:
            customer = customer_credit_id.credit_id.credit_line.filtered(lambda l: l.sale_team_id == self.team_id)
            if customer:
                self.payment_term_id = customer.payment_term_id.id
                self.payment_method_id = customer.payment_method_id.id
                self.billing_period_id = customer.billing_period_id.id
            else:
                self.payment_term_id = False
                self.payment_method_id = False
                self.billing_period_id = False
        else:
            self.payment_term_id = self.partner_id.property_payment_term_id.id
            self.payment_method_id = False
            self.billing_period_id = self.partner_id.billing_period_id.id

    can_edit_payment_terms = fields.Boolean(
        compute='_compute_can_edit_payment_terms',
        store=False,
    )

    @api.depends('user_id')
    def _compute_can_edit_payment_terms(self):
        for order in self:
            order.can_edit_payment_terms = self.env.user.has_group('hdc_creditlimit_saleteam.group_can_change_payment_terms')

    @api.onchange('can_edit_payment_terms')
    def _onchange_payment_term_domain(self):
        if not self.can_edit_payment_terms:
            return {
                'domain': {
                    'payment_term_id': [('is_cash', '=', True)]
                }
            }
        else:
            return {
                'domain': {
                    'payment_term_id': []
                }
            }