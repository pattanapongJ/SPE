# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import re
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang
from collections import defaultdict

class Quotations(models.Model):
    _inherit = 'quotation.order'

    promotion_ids = fields.One2many(
        'coupon.program',
        string='Promotions Can Use', 
        compute='_compute_promotions', 
        store=False
    )
    promotion_id = fields.Many2one('coupon.program', string='Promotion', 
        domain="[('reward_type', 'in', ['discount', 'free_shipping']), ('discount_apply_on', '=', 'on_order'), ('company_id', 'in', company_id)]"
        # domain="['&', '&', ('reward_type', 'in', ['discount', 'free_shipping']), ('discount_apply_on', '=', 'on_order'), '|', ('company_id', '=', False), ('company_id', 'in', company_id)]"
    )
    applied_coupon_ids = fields.One2many('coupon.coupon', 'sales_quotation_order_id', string="Applied Coupons", copy=False)
    generated_coupon_ids = fields.One2many('coupon.coupon', 'quotation_order_id', string="Offered Coupons", copy=False)
    reward_amount = fields.Float(compute='_compute_reward_total')
    no_code_promo_program_ids = fields.Many2many('coupon.program', string="Applied Immediate Promo Programs",
        domain="[('promo_code_usage', '=', 'no_code_needed'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", copy=False)
    code_promo_program_id = fields.Many2one('coupon.program', string="Applied Promo Program",
        domain="[('promo_code_usage', '=', 'code_needed'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", copy=False)
    promo_code = fields.Char(related='code_promo_program_id.promo_code', help="Applied program code", readonly=False)

    @api.depends('quotation_line.product_id', 'pricelist_id')
    def _compute_promotions(self):
        for order in self:
            programs = order._get_applicable_no_code_promo_program()
            # programs = programs._keep_only_most_interesting_auto_applied_global_discount_program()
            promotion_ids = order.env['coupon.program']
            if programs and order.promotion_id is False:
                promotion_ids = programs.ids
                # if not order.promotion_id or order.promotion_id not in programs:
                #     order.promotion_id = programs[0]
            # else:
            #     order.promotion_id = False
            order.promotion_ids = promotion_ids


    @api.onchange('company_id')
    def _get_promotion_domain(self):
        if self.company_id:
            return {
                'domain': {
                    'promotion_id': [
                        ('reward_type', 'in', ['discount', 'free_shipping']),
                        '|',
                        ('company_id', '=', False),
                        ('company_id', 'in', self.company_id.ids)
                    ]
                }
            }
        return {'domain': {'promotion_id': []}} 
    
    def _create_new_no_code_promo_reward_lines(self):
        '''Apply new programs that are applicable'''
        self.ensure_one()
        order = self
        promotion_ids = order.quotation_line.mapped("promotion_id")
        promotion_ids |= order.promotion_id
        programs = promotion_ids
        Check_apply = self._get_applicable_no_code_promo_program()
        # programs = programs._keep_only_most_interesting_auto_applied_global_discount_program()
        for program in programs.filtered(lambda p: p.id in Check_apply.ids):
            error_status = program._check_promo_code_quotation(order, False)
            if not error_status.get('error'):
                if program.promo_applicability == 'on_next_order':
                    order.state != 'cancel' and order._create_reward_coupon(program)
                if program.reward_type == 'product':
                    self.write({'quotation_line': [(0, False, value) for value in self._get_reward_line_values(program)]})
                order.no_code_promo_program_ids |= program

    def _get_applicable_no_code_promo_program(self):
        self.ensure_one()
        programs = self.env['coupon.program'].with_context(
            no_outdated_coupons=True,
            applicable_coupon=True,
        ).search([
            ('promo_code_usage', '=', 'no_code_needed'),
            '|', ('rule_date_from', '=', False), ('rule_date_from', '<=', fields.Datetime.now()),
            '|', ('rule_date_to', '=', False), ('rule_date_to', '>=', fields.Datetime.now()),
            '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False),
            '|', ('pricelists', '=', False),('pricelists', 'in', self.pricelist_id.ids),
        ], order='create_date desc')._filter_programs_from_common_rules_quotation_order(self)
        return programs
    
    def _get_reward_values_product(self, program):
        order_lines = (self.quotation_line - self._get_reward_lines()).filtered(lambda x: program._get_valid_products(x.product_id))
        order_lines = order_lines.filtered(lambda x: x.free_product is False)
        max_product_qty = sum(order_lines.mapped('product_uom_qty')) or 1
        total_qty = sum(self.quotation_line.filtered(lambda x: x.product_id == program.reward_product_id).mapped('product_uom_qty'))
        program_in_order = max_product_qty // (program.rule_min_quantity)
        reward_product_qty = program.reward_product_quantity * program_in_order
        if program.rule_minimum_amount:
            order_total = self.amount_total
            reward_product_qty = min(reward_product_qty, order_total // program.rule_minimum_amount)
            if program.maximum_use_free_product:
                reward_product_qty = min(reward_product_qty, program.maximum_use_free_product)
        reward_qty = min(int(int(max_product_qty / program.rule_min_quantity) * program.reward_product_quantity), reward_product_qty)
        return {
            'product_id': program.discount_line_product_id.id,
            'price_unit': 0.0,  # กำหนดราคาเป็น 0 สำหรับของแถม
            'product_uom_qty': reward_qty,  # จำนวนสินค้าที่จะแถม
            'is_reward_line': True,
            'name': _("Free Product") + " - " + program.reward_product_id.name,
            'product_uom': program.reward_product_id.uom_id.id,
        }
    
    def _update_existing_reward_lines(self):
        '''Update values for already applied rewards'''
        def update_line(order, lines, values):
            '''Update the lines and return them if they should be deleted'''
            lines_to_remove = self.env['quotation.order.line']
            values['sequence'] = max(order.quotation_line.mapped('sequence')) + 1

            if values['product_uom_qty'] and (values['price_unit'] or values['price_unit'] == 0): #ยอมให้ราคา0ผ่านไป
                lines.write(values)
            else:
                if program.reward_type != 'free_shipping':
                    lines_to_remove += lines
                else:
                    values.update(price_unit=0.0)
                    lines.write(values)
            return lines_to_remove

        self.ensure_one()
        order = self
        applied_programs = order._get_applied_programs_with_rewards_on_current_order()
        Check_apply = self._get_applicable_no_code_promo_program()
        applied_programs = applied_programs.filtered(lambda ap: ap.id in Check_apply.ids)
        for program in applied_programs.sorted(lambda ap: (ap.discount_type == 'fixed_amount', ap.discount_apply_on == 'on_order')):
            values = order._get_reward_line_values(program)
            lines = order.quotation_line.filtered(lambda line: line.product_id == program.discount_line_product_id)
            if program.reward_type == 'discount':
                lines_to_remove = lines
                lines_to_add = []
                lines_to_keep = []
                for value in values:
                    value_found = False
                    for line in lines:
                        if not len(set(line.tax_id.mapped('id')).symmetric_difference(set([v[1] for v in value['tax_id']]))):
                            value_found = True
                            update_to_remove = update_line(order, line, value)
                            if not update_to_remove:
                                lines_to_keep += [(0, False, value)]
                                lines_to_remove -= line
                    if not value_found:
                        lines_to_add += [(0, False, value)]
                line_update = []
                if lines_to_remove:
                    line_update += [(3, line_id, 0) for line_id in lines_to_remove.ids]
                    line_update += lines_to_keep
                line_update += lines_to_add
                order.write({'quotation_line': line_update})
            else:
                update_line(order, lines, values[0]).unlink()

    def _get_reward_values_percentage_amount(self, program):
        fixed_price_products = self._get_applied_programs().filtered(
            lambda p: p.discount_type == 'fixed_amount'
        ).mapped('discount_line_product_id')
        self.quotation_line.filtered(lambda l: l.product_id in fixed_price_products).write({'price_unit': 0})

        reward_dict = {}
        lines = self._get_paid_order_lines()
        amount_total = sum([any(line.tax_id.mapped('price_include')) and line.price_total or line.price_subtotal
                            for line in self._get_base_order_lines(program)]) 
        if program.discount_apply_on in ['cheapest_product','specific_products']:
            line = self._get_cheapest_line()
            if program.discount_apply_on == 'specific_products':
                line = lines.filtered(lambda x: x.product_id in (program.discount_specific_product_ids ))
                for l in lines:
                    discount_line_amount = min((l.price_reduce * l.product_uom_qty) * (program.discount_percentage / 100), amount_total)
                    if discount_line_amount:
                        l.promotion_discount = discount_line_amount
            else:
                if line:
                    discount_line_amount = min((line.price_reduce * line.product_uom_qty) * (program.discount_percentage / 100), amount_total)
                    if discount_line_amount:
                        line.promotion_discount = discount_line_amount
        else:
            currently_discounted_amount = 0
            for line in lines:
                discount_line_amount = min(self._get_reward_values_discount_percentage_per_line(program, line), amount_total - currently_discounted_amount)
                if discount_line_amount:

                    if line.tax_id in reward_dict:
                        reward_dict[line.tax_id]['price_unit'] -= discount_line_amount
                    else:
                        taxes = self.fiscal_position_id.map_tax(line.tax_id)

                        reward_dict[line.tax_id] = {
                            'name': _(
                                "Discount: %(program)s - On product with following taxes: %(taxes)s",
                                program=program.name,
                                taxes=", ".join(taxes.mapped('name')),
                            ),
                            'product_id': program.discount_line_product_id.id,
                            'price_unit': - discount_line_amount if discount_line_amount > 0 else 0,
                            'product_uom_qty': 1.0,
                            'product_uom': program.discount_line_product_id.uom_id.id,
                            'is_reward_line': True,
                            'tax_id': [(4, tax.id, False) for tax in taxes],
                        }
                        currently_discounted_amount += discount_line_amount

        # If there is a max amount for discount, we might have to limit some discount lines or completely remove some lines
        max_amount = program._compute_program_amount('discount_max_amount', self.currency_id)
        if max_amount > 0:
            amount_already_given = 0
            for val in list(reward_dict):
                amount_to_discount = amount_already_given + reward_dict[val]["price_unit"]
                if abs(amount_to_discount) > max_amount:
                    reward_dict[val]["price_unit"] = - (max_amount - abs(amount_already_given))
                    add_name = formatLang(self.env, max_amount, currency_obj=self.currency_id)
                    reward_dict[val]["name"] += "( " + _("limited to ") + add_name + ")"
                amount_already_given += reward_dict[val]["price_unit"]
                if reward_dict[val]["price_unit"] == 0:
                    del reward_dict[val]
        return reward_dict.values()

    def _get_reward_values_fixed_amount(self, program):
        discount_amount = self._get_reward_values_discount_fixed_amount(program)

        # In case there is a tax set on the promotion product, we give priority to it.
        # This allow manual overwrite of taxes for promotion.
        if program.discount_line_product_id.taxes_id:
            line_taxes = self.fiscal_position_id.map_tax(program.discount_line_product_id.taxes_id) if self.fiscal_position_id else program.discount_line_product_id.taxes_id
            lines = self._get_base_order_lines(program)
            discount_amount = min(
                sum(lines.mapped(lambda l: l.price_reduce * l.product_uom_qty)), discount_amount
            )
            return [{
                'name': _("Discount: %s", program.name),
                'product_id': program.discount_line_product_id.id,
                'price_unit': -discount_amount,
                'product_uom_qty': 1.0,
                'product_uom': program.discount_line_product_id.uom_id.id,
                'is_reward_line': True,
                'tax_id': [(4, tax.id, False) for tax in line_taxes],
            }]

        lines = self._get_paid_order_lines()
        # Remove Free Lines
        lines = lines.filtered('price_reduce')
        reward_lines = {}

        tax_groups = set([line.tax_id for line in lines])
        max_discount_per_tax_groups = {tax_ids: self._get_max_reward_values_per_tax(program, tax_ids) for tax_ids in tax_groups}

        for tax_ids in sorted(tax_groups, key=lambda tax_ids: max_discount_per_tax_groups[tax_ids], reverse=True):

            if discount_amount <= 0:
                return reward_lines.values()

            curr_lines = lines.filtered(lambda l: l.tax_id == tax_ids)
            lines_price = sum(curr_lines.mapped(lambda l: l.price_reduce * l.product_uom_qty ))
            lines_total = sum(curr_lines.mapped('price_total'))

            discount_line_amount_price = min(max_discount_per_tax_groups[tax_ids], (discount_amount))

            if not discount_line_amount_price:
                continue

            # discount_amount -= discount_line_amount_price * lines_total / lines_price

            reward_lines[tax_ids] = {
                'name': _(
                    "Discount: %(program)s - On product with following taxes: %(taxes)s",
                    program=program.name,
                    taxes=", ".join(tax_ids.mapped('name')),
                ),
                'product_id': program.discount_line_product_id.id,
                'price_unit': -discount_line_amount_price,
                'product_uom_qty': 1.0,
                'product_uom': program.discount_line_product_id.uom_id.id,
                'is_reward_line': True,
                'tax_id': [(4, tax.id, False) for tax in tax_ids],
                }
        return reward_lines.values()

    def _remove_invalid_reward_lines(self):
        self.ensure_one()
        order = self
        invalid_lines = order.quotation_line.filtered(lambda line: line.is_reward_line)
        for line in order.quotation_line:
            line.write({'promotion_discount': 0})
        invalid_lines.unlink()

    @api.depends('quotation_line')
    def _compute_reward_total(self):
        for order in self:
            order.reward_amount = sum([line.price_subtotal for line in order._get_reward_lines()])

    def _get_no_effect_on_threshold_lines(self):
        self.ensure_one()
        lines = self.env['sale.order.line']
        return lines

    def recompute_coupon_lines(self):
        for order in self:
            order._remove_invalid_reward_lines()
            if order.state != 'cancel':
                order._create_new_no_code_promo_reward_lines()
            order._update_existing_reward_lines()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        order = super(Quotations, self).copy(default)
        reward_line = order._get_reward_lines()
        if reward_line:
            reward_line.unlink()
            order._create_new_no_code_promo_reward_lines()
        return order

    def _get_reward_lines(self):
        self.ensure_one()
        return self.quotation_line.filtered(lambda line: line.is_reward_line)

    def _is_reward_in_order_lines(self, program):
        self.ensure_one()
        order_quantity = sum(self.quotation_line.filtered(lambda line:
            line.product_id == program.reward_product_id).mapped('product_uom_qty'))
        return order_quantity >= program.reward_product_quantity

    def _is_global_discount_already_applied(self):
        applied_programs = self.no_code_promo_program_ids + \
                           self.code_promo_program_id + \
                           self.applied_coupon_ids.mapped('program_id')
        return applied_programs.filtered(lambda program: program._is_global_discount_program())


    def _get_paid_order_lines(self):
        """ Returns the sale order lines that are not reward lines.
            It will also return reward lines being free product lines. """
        free_reward_product = self.env['coupon.program'].search([('reward_type', '=', 'product')]).mapped('discount_line_product_id')
        return self.quotation_line.filtered(lambda x: not x.is_reward_line or x.product_id in free_reward_product)

    def _get_base_order_lines(self, program):
        """ Returns the sale order lines not linked to the given program.
        """
        return self.quotation_line.filtered(lambda x: not (x.is_reward_line and x.product_id == program.discount_line_product_id))

    def _get_reward_values_discount_fixed_amount(self, program):
        total_amount = sum(self._get_base_order_lines(program).mapped('price_total'))
        fixed_amount = program._compute_program_amount('discount_fixed_amount', self.currency_id)
        if total_amount < fixed_amount:
            return total_amount
        else:
            return fixed_amount

    def _get_coupon_program_domain(self):
        return []

    def _get_cheapest_line(self):
        # Unit prices tax included
        return min(self.quotation_line.filtered(lambda x: not x.is_reward_line and x.price_reduce > 0), key=lambda x: x['price_reduce'])

    def _get_reward_values_discount_percentage_per_line(self, program, line):
        discount_amount = line.product_uom_qty * line.price_reduce * (program.discount_percentage / 100)
        return discount_amount

    def _get_max_reward_values_per_tax(self, program, taxes):
        lines = self.quotation_line.filtered(lambda l: l.tax_id == taxes and l.product_id != program.discount_line_product_id)
        return sum(lines.mapped(lambda l: l.price_reduce * l.product_uom_qty))

    def _get_reward_values_discount(self, program):
        if program.discount_type == 'fixed_amount':
            return self._get_reward_values_fixed_amount(program)
        else:
            return self._get_reward_values_percentage_amount(program)

    def _get_reward_line_values(self, program):
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        program = program.with_context(lang=self.partner_id.lang)
        values = []
        if program.reward_type == 'discount':
            values = self._get_reward_values_discount(program)
        elif program.reward_type == 'product':
            values = [self._get_reward_values_product(program)]
        seq = max(self.quotation_line.mapped('sequence'), default=10) + 1
        for value in values:
            value['sequence'] = seq
        return values

    def _create_reward_line(self, program):
        self.write({'quotation_line': [(0, False, value) for value in self._get_reward_line_values(program)]})

    def _create_reward_coupon(self, program):
        # if there is already a coupon that was set as expired, reactivate that one instead of creating a new one
        coupon = self.env['coupon.coupon'].search([
            ('program_id', '=', program.id),
            ('state', '=', 'expired'),
            ('partner_id', '=', self.partner_id.id),
            ('quotation_order_id', '=', self.id),
            ('discount_line_product_id', '=', program.discount_line_product_id.id),
        ], limit=1)
        if coupon:
            coupon.write({'state': 'reserved'})
        else:
            coupon = self.env['coupon.coupon'].sudo().create({
                'program_id': program.id,
                'state': 'reserved',
                'partner_id': self.partner_id.id,
                'quotation_order_id': self.id,
                'discount_line_product_id': program.discount_line_product_id.id
            })
        self.generated_coupon_ids |= coupon
        return coupon

    def _send_reward_coupon_mail(self):
        template = self.env.ref('coupon.mail_template_sale_coupon', raise_if_not_found=False)
        if template:
            for order in self:
                for coupon in order.generated_coupon_ids.filtered(lambda coupon: coupon.state == 'new'):
                    order.message_post_with_template(
                        template.id, composition_mode='comment',
                        model='coupon.coupon', res_id=coupon.id,
                        email_layout_xmlid='mail.mail_notification_light',
                    )

    def _get_applicable_programs(self):
        """
        This method is used to return the valid applicable programs on given order.
        """
        self.ensure_one()
        programs = self.env['coupon.program'].with_context(
            no_outdated_coupons=True,
        ).search([
            ('company_id', 'in', [self.company_id.id, False]),
            '|', ('rule_date_from', '=', False), ('rule_date_from', '<=', fields.Datetime.now()),
            '|', ('rule_date_to', '=', False), ('rule_date_to', '>=', fields.Datetime.now()),
        ], order="id")._filter_programs_from_common_rules_quotation_order(self)
        # no impact code...
        # should be programs = programs.filtered if we really want to filter...
        # if self.promo_code:
        #     programs._filter_promo_programs_with_code(self)
        return programs

    def _get_valid_applied_coupon_program(self):
        self.ensure_one()
        # applied_coupon_ids's coupons might be coming from:
        #   * a coupon generated from a previous order that benefited from a promotion_program that rewarded the next sale order.
        #     In that case requirements to benefit from the program (Quantity and price) should not be checked anymore
        #   * a coupon_program, in that case the promo_applicability is always for the current order and everything should be checked (filtered)
        programs = self.applied_coupon_ids.mapped('program_id').filtered(lambda p: p.promo_applicability == 'on_next_order')._filter_programs_from_common_rules_quotation_order(self, True)
        programs += self.applied_coupon_ids.mapped('program_id').filtered(lambda p: p.promo_applicability == 'on_current_order')._filter_programs_from_common_rules_quotation_order(self)
        return programs

    def _get_applied_programs_with_rewards_on_current_order(self):
        return self.no_code_promo_program_ids.filtered(lambda p: p.promo_applicability == 'on_current_order') + \
               self.applied_coupon_ids.mapped('program_id') + \
               self.code_promo_program_id.filtered(lambda p: p.promo_applicability == 'on_current_order')

    def _get_applied_programs_with_rewards_on_next_order(self):
        return self.no_code_promo_program_ids.filtered(lambda p: p.promo_applicability == 'on_next_order') + \
            self.code_promo_program_id.filtered(lambda p: p.promo_applicability == 'on_next_order')

    def _get_applied_programs(self):
        return self.code_promo_program_id + self.no_code_promo_program_ids + self.applied_coupon_ids.mapped('program_id')

    def _get_invoice_status(self):
        super()._get_invoice_status()
        for order in self.filtered(lambda order: order.invoice_status == 'to invoice'):
            paid_lines = order._get_paid_order_lines()
            if not any(line.invoice_status == 'to invoice' for line in paid_lines):
                order.invoice_status = 'no'

    def _get_invoiceable_lines(self, final=False):
        invoiceable_lines = super()._get_invoiceable_lines(final)
        reward_lines = self._get_reward_lines()
        if invoiceable_lines <= reward_lines:
            return self.env['sale.order.line'].browse()
        return invoiceable_lines
    
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
                        'is_global_discount': line.is_global_discount,
                        'promotion_discount': line.promotion_discount,
                        'is_reward_line': line.is_reward_line,
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
    

class QuotationLine(models.Model):
    _inherit = 'quotation.order.line'
    
    promotion_discount = fields.Float(string="Discount Promotion", digits='Product Price')
    is_reward_line = fields.Boolean('Is a program reward line')
    price_reduce = fields.Float(compute='_get_price_reduce', string='Price Reduce', digits='Product Price', readonly=True, store=True)
    promotion_id = fields.Many2one(
        'coupon.program', 
        string='Promotion', 
        domain="['&', '|', '&', ('valid_product_ids', 'in', product_id), ('reward_type', 'in', ['product']), '&','&', ('reward_type', '=', 'discount'), ('discount_apply_on', '=', 'specific_products'), ('discount_specific_product_ids', 'in', product_id), ('company_id', 'in', company_id)]"
    )

    def _get_latest_promotion(self, product):
        domain = [
            '&',
                '|',    
                    '&', 
                        ('reward_type', '=', 'product'),
                        ('valid_product_ids', 'in', product.id),
                    '&', '&',
                        ('reward_type', '=', 'discount'),
                        ('discount_apply_on', '=', 'specific_products'),
                        ('discount_specific_product_ids', 'in', product.id),
                ('company_id', 'in', self.company_id.ids),
        ]
        return self.env['coupon.program'].search(domain, order="create_date desc", limit=1)

    @api.onchange('product_id')
    def _onchange_product_id_promotion(self):
        # if not self.promotion_id:
            latest_promotion = self._get_latest_promotion(self.product_id)
            self.promotion_id = latest_promotion if latest_promotion else False
    
    @api.constrains('price_subtotal')
    def _check_price_subtotal(self):
        for line in self:
            if line.price_subtotal < 0 and line.is_global_discount is False and line.is_reward_line is False:
                raise UserError('Subtotal cannot be negative. Please check the order lines.')
            
    @api.constrains('price_total')
    def _check_price_total(self):
        for line in self:
            if line.price_total < 0 and line.is_global_discount is False and line.is_reward_line is False:
                raise UserError('Net Amount cannot be negative. Please check the order lines.')
       
    @api.depends('price_unit', 'discount')
    def _get_price_reduce(self):
        for line in self:
            line.price_reduce = line.price_unit * (1.0 - line.discount / 100.0)

    def unlink(self):
        related_program_lines = self.env['quotation.order.line']
        # Reactivate coupons related to unlinked reward line
        for line in self.filtered(lambda line: line.is_reward_line):
            coupons_to_reactivate = line.quotation_id.applied_coupon_ids.filtered(
                lambda coupon: coupon.program_id.discount_line_product_id == line.product_id
            )
            coupons_to_reactivate.write({'state': 'new'})
            line.quotation_id.applied_coupon_ids -= coupons_to_reactivate
            # Remove the program from the order if the deleted line is the reward line of the program
            # And delete the other lines from this program (It's the case when discount is split per different taxes)
            related_program = self.env['coupon.program'].search([('discount_line_product_id', '=', line.product_id.id)])
            if related_program:
                line.quotation_id.no_code_promo_program_ids -= related_program
                line.quotation_id.code_promo_program_id -= related_program
                related_program_lines |= line.quotation_id.quotation_line.filtered(lambda l: l.product_id.id == related_program.discount_line_product_id.id) - line
        return super(QuotationLine, self | related_program_lines).unlink()


    @api.depends('triple_discount', 'product_uom_qty', 'price_unit', 'tax_id', 'dis_price', 'rounding_price','promotion_discount')
    def _compute_amount(self): # (การทำงานล่าสุด 29/08/2025)
        for line in self:
            total_dis = 0.0
            price_total = (line.price_unit * line.product_uom_qty)
            price_total = price_total - line.promotion_discount
            if line.triple_discount:
                try:
                    discounts = line.triple_discount.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                    for discount in discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for discount in discounts:
                        if discount.endswith("%"):
                            dis_percen = discount.replace("%", "")
                            total_percen = ((price_total) * float(dis_percen)) / 100
                            price_total -= total_percen
                            total_dis += total_percen
                        else:
                            total_baht = float(discount) * line.product_uom_qty
                            price_total -= total_baht
                            total_dis += total_baht
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))

            price = (line.price_unit * line.product_uom_qty) - line.promotion_discount - total_dis
            
            if line.rounding_price:
                try:
                    rounding_value = float(line.rounding_price[1:])
                    decimal_precision = self.env['decimal.precision'].precision_get('Sale Rounding')
                    rounding_pattern = re.compile(r'^[+-]?\d+(\.\d{1,%d})?$' % decimal_precision)
                    
                    if not rounding_pattern.match(line.rounding_price):
                        raise ValidationError(_('Invalid Rounding format : +20 or -20 with up to %d decimal places' % decimal_precision))

                    if line.rounding_price.startswith("+"):
                        price += rounding_value
                    elif line.rounding_price.startswith("-"):
                        price -= rounding_value
                    else:
                        raise ValidationError(_('Invalid Rounding format : +20 or -20'))
                except:
                    raise ValidationError(_('Invalid Rounding format : +20 or -20'))

            taxes = line.tax_id.compute_all(price, line.quotation_id.currency_id, 1, product=line.product_id, partner=line.quotation_id.partner_shipping_id)
            
            if line.tax_id.price_include:
                price_total = taxes['total_included']
            else:
                price_total = taxes['total_excluded']

            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': price_total,
                'price_subtotal': taxes['total_excluded'],
                'dis_price': total_dis,
            })
                        
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_quotation_line'], [line.tax_id.id])
    
    def modified(self, fnames, *args, **kwargs):
        super(QuotationLine, self).modified(fnames, *args, **kwargs)
        if 'product_id' in fnames:
            Program = self.env['coupon.program'].sudo()
            field_order_count = Program._fields['order_count']
            programs = self.env.cache.get_records(Program, field_order_count)
            if programs:
                products = self.filtered('is_reward_line').mapped('product_id')
                for program in programs:
                    if program.discount_line_product_id in products:
                        self.env.cache.invalidate([(field_order_count, program.ids)])
 