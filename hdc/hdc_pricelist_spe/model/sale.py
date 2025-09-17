# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import formatLang, get_lang

class SaleOrder(models.Model):
    _inherit = "sale.order"

    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
        required=False, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id),('id','in',pricelist_ids)]", 
        tracking=1, help="If you change the pricelist, only newly added lines will be affected.")

    pricelist_ids = fields.One2many('product.pricelist', compute='_compute_pricelist_ids')
    currency_id = fields.Many2one('res.currency', related=False, store = True, domain = [('rate_type','=', 'buy')])

    @api.depends('partner_id', 'user_id', 'type_id')
    def _compute_pricelist_ids(self):
        for order in self:
            all_pricelists = self.env['product.pricelist'].browse([])
            partner = order.partner_id

            # Master Pricelist
            domain_master_pricelist = [
                ('is_default', '=', True),
                ('partner_id', '=', order.partner_id.id)
            ]
            pricelists_master = self.env['product.pricelist.customer'].search(domain_master_pricelist)
            if pricelists_master:
                all_pricelists |= pricelists_master.mapped('pricelist_id')

            # Master Customer
            if partner.parent_id:
                partner = partner.parent_id

            if partner.pricelist_ids:
                all_pricelists |= partner.pricelist_ids

            elif partner.property_product_pricelist:
                all_pricelists |= partner.property_product_pricelist

            # Pricelist All
            if not all_pricelists:
                pricelist_all = self.env['product.pricelist'].search([('pricelist_all', '=', True)])
                all_pricelists |= pricelist_all

            # Sale Type
            if order.type_id and order.type_id.pricelist_id:
                pricelist_from_sale_type = order.type_id.pricelist_id
                exists = self.env['product.pricelist.customer'].search_count([
                    ('partner_id', '=', order.partner_id.id),
                    ('pricelist_id', '=', pricelist_from_sale_type.id)
                ])
                if exists:
                    all_pricelists |= pricelist_from_sale_type

            order.pricelist_ids = all_pricelists
            # order.pricelist_id = all_pricelists[0].id if all_pricelists else False

    @api.onchange('partner_id', 'user_id', 'type_id')
    def _onchange_pricelist_id(self):
        for order in self:
            all_pricelists = self.env['product.pricelist'].browse([])
            partner = order.partner_id

            # Master Pricelist
            domain_master_pricelist = [
                ('is_default', '=', True),
                ('partner_id', '=', order.partner_id.id)
            ]
            pricelists_master = self.env['product.pricelist.customer'].search(domain_master_pricelist)
            if pricelists_master:
                all_pricelists |= pricelists_master.mapped('pricelist_id')

            # Master Customer
            if partner.parent_id:
                partner = partner.parent_id

            if partner.pricelist_ids:
                all_pricelists |= partner.pricelist_ids

            elif partner.property_product_pricelist:
                all_pricelists |= partner.property_product_pricelist

            # Pricelist All
            if not all_pricelists:
                pricelist_all = self.env['product.pricelist'].search([('pricelist_all', '=', True)])
                all_pricelists |= pricelist_all

            # Sale Type
            if order.type_id and order.type_id.pricelist_id:
                pricelist_from_sale_type = order.type_id.pricelist_id
                exists = self.env['product.pricelist.customer'].search_count([
                    ('partner_id', '=', order.partner_id.id),
                    ('pricelist_id', '=', pricelist_from_sale_type.id)
                ])
                if exists:
                    all_pricelists |= pricelist_from_sale_type

            if len(all_pricelists) > 0:
                if order.pricelist_id != all_pricelists[0]:
                    if order.pricelist_id not in all_pricelists:
                        order.pricelist_id = all_pricelists[0] if all_pricelists else False
    
    @api.onchange('pricelist_id')
    def _onchange_pricelist_to_change_fiscal_position_id(self):
        self.currency_id = self.pricelist_id.currency_id.id
        if self.order_line and self.pricelist_id and self._origin.pricelist_id != self.pricelist_id:
            self.show_update_pricelist = True
        else:
            self.show_update_pricelist = False
        for order in self:
            fiscal_position_id = order.pricelist_id.fiscal_position_id
            if fiscal_position_id :
                order.fiscal_position_id = fiscal_position_id
                

class SalesOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('price_unit')
    def _onchange_sale_order_line(self):
        for order_line in self :
            if order_line.order_id.type_id.is_oversea:
                break
            pricelist_id = self.env["product.pricelist.item"].search([("product_tmpl_id","=",order_line.product_id.product_tmpl_id.id),("pricelist_id","=",order_line.order_id.pricelist_id.id)],limit=1)
            if pricelist_id.net_price:
                order_line.price_unit = pricelist_id.fixed_price
                order_line.with_context(skip_net_price_update=True)

    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        # awa: don't know if it's still the case since we need the "product_no_variant_attribute_value_ids" field now
        # to be able to compute the full price

        # it is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.
        no_variant_attributes_price_extra = [ptav.price_extra for ptav in
            self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav: ptav.price_extra and ptav not in product.product_template_attribute_value_ids)]
        if no_variant_attributes_price_extra:
            product = product.with_context(no_variant_attributes_price_extra = tuple(no_variant_attributes_price_extra))

        item_product = self.order_id.pricelist_id.item_ids
        check_product = item_product.filtered(lambda l: l.product_tmpl_id == self.product_template_id) or item_product.filtered(lambda l: l.product_id == self.product_id)
        pricelist_id = self.order_id.pricelist_id
        if not check_product:
            pricelist_all = self.env["product.pricelist"].search([("pricelist_all", "=", True)],limit=1)
            if pricelist_all:
                pricelist_id = pricelist_all

        if pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist = pricelist_id.id, uom = self.product_uom.id).price
        product_context = dict(self.env.context, partner_id = self.order_id.partner_id.id,
                               date = self.order_id.date_order, uom = self.product_uom.id)

        final_price, rule_id = pricelist_id.with_context(product_context).get_product_price_rule(
            product or self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                           self.product_uom_qty,
                                                                                           self.product_uom,
                                                                                           pricelist_id.id)
        if currency != pricelist_id.currency_id:
            base_price = currency._convert(base_price, pricelist_id.currency_id,
                self.order_id.company_id or self.env.company, self.order_id.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)