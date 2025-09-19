from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang
import re
from odoo.tools import float_round

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sales Order'

    promotion_ids = fields.One2many(
        'coupon.program',
        string='Promotions Can Use', 
        compute='_compute_promotions', 
        store=False
    )
    promotion_id = fields.Many2one(
        'coupon.program', 
        string='Promotion', 
        domain="[('reward_type', 'in', ['discount', 'free_shipping']), ('discount_apply_on', '=', 'on_order'), ('company_id', 'in', company_id)]"

    )
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
        return {'domain': {'promotion_id': []}}  # กรณีไม่มี company_id

    @api.depends('order_line.product_id', 'pricelist_id')
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


    # @api.onchange('promotion_id','promotion_ids','pricelist_id')
    # def _get_promotion_domain(self):
    #     for order in self:
    #         return {
    #             "domain": {
    #                 "promotion_id": [('id', 'in', order.promotion_ids.ids)],
    #                 }
    #             }
    
    def _create_new_no_code_promo_reward_lines(self):
        '''Apply new programs that are applicable'''
        self.ensure_one()
        order = self
        promotion_ids = order.order_line.mapped("promotion_id")
        promotion_ids |= order.promotion_id
        programs = promotion_ids
        Check_apply = self._get_applicable_no_code_promo_program()
        # programs = programs._keep_only_most_interesting_auto_applied_global_discount_program()
        for program in programs.filtered(lambda p: p.id in Check_apply.ids):
            error_status = program._check_promo_code(order, False)
            if not error_status.get('error'):
                if program.promo_applicability == 'on_next_order':
                    order.state != 'cancel' and order._create_reward_coupon(program)
                if program.reward_type == 'product':
                    self.write({'order_line': [(0, False, value) for value in self._get_reward_line_values(program)]})
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
            '|', ('company_id', 'in', self.company_id.ids), ('company_id', '=', False),
            '|', ('sale_team_ids', '=', False), ('sale_team_ids', 'in', self.team_id.ids),
            '|', ('pricelists', '=', False),('pricelists', 'in', self.pricelist_id.ids),
        ], order='create_date desc')._filter_programs_from_common_rules(self)
        return programs
    
    def _get_reward_values_product(self, program):
        order_lines = (self.order_line - self._get_reward_lines()).filtered(lambda x: program._get_valid_products(x.product_id))
        order_lines = order_lines.filtered(lambda x: x.free_product is False)
        max_product_qty = sum(order_lines.mapped('product_uom_qty')) or 1
        total_qty = sum(self.order_line.filtered(lambda x: x.product_id == program.reward_product_id).mapped('product_uom_qty'))
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
            lines_to_remove = self.env['sale.order.line']
            values['sequence'] = max(order.order_line.mapped('sequence')) + 1

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
            lines = order.order_line.filtered(lambda line: line.product_id == program.discount_line_product_id)
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
                order.write({'order_line': line_update})
            else:
                update_line(order, lines, values[0]).unlink()

    def _get_reward_values_percentage_amount(self, program):
        fixed_price_products = self._get_applied_programs().filtered(
            lambda p: p.discount_type == 'fixed_amount'
        ).mapped('discount_line_product_id')
        self.order_line.filtered(lambda l: l.product_id in fixed_price_products).write({'price_unit': 0})

        reward_dict = {}
        lines = self._get_paid_order_lines()
        amount_total = sum([any(line.tax_id.mapped('price_include')) and line.price_total or line.price_subtotal
                            for line in self._get_base_order_lines(program)]) 
        
        if program.discount_apply_on in ['cheapest_product','specific_products']:
            line = self._get_cheapest_line()
            if program.discount_apply_on == 'specific_products':
                line = lines.filtered(lambda x: x.product_id in (program.discount_specific_product_ids ))
            if line:
                if program.discount_type == 'formula':
                    precision = self.env['decimal.precision'].precision_get('Product Price')
                    amount_untaxed = (line.price_reduce * line.product_uom_qty)
                    discount_line_amount = 0.0
                    discounts = program.formula_discount.replace(" ", "").split("+")
                    for discount in discounts:
                        if discount.endswith("%"):
                            dis_percen = discount.replace("%", "")
                            discount_amount = float_round(((amount_untaxed * float(dis_percen)) / 100), precision_digits=precision)
                            amount_untaxed -= discount_amount
                            discount_line_amount += discount_amount
                        else:
                            discount_amount = float_round(float(discount), precision_digits=precision)
                            amount_untaxed -= discount_amount
                            discount_line_amount += discount_amount
                    if program.discount_max_amount > 0:
                        discount_line_amount = min(discount_line_amount, program.discount_max_amount)
                    discount_line_amount = min(discount_line_amount, amount_total)
                else:
                    discount_line_amount = min((line.price_reduce * line.product_uom_qty) * (program.discount_percentage / 100), amount_total)
                    if program.discount_max_amount > 0:
                        discount_line_amount = min(discount_line_amount, program.discount_max_amount)

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
        invalid_lines = order.order_line.filtered(lambda line: line.is_reward_line)
        for line in order.order_line:
            line.write({'promotion_discount': 0})
        invalid_lines.unlink()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sales Order Line'
    
    promotion_discount = fields.Float(string="Discount Promotion", digits='Product Price')
    promotion_id = fields.Many2one(
        'coupon.program', 
        string='Promotion', 
        domain="['&', '|', '&', ('valid_product_ids', 'in', product_id), ('reward_type', 'in', ['product']), '&', '&', ('reward_type', '=', 'discount'), ('discount_apply_on', '=', 'specific_products'), ('discount_specific_product_ids', 'in', product_id), ('company_id', 'in', company_id)]"
    )
    formula_discount = fields.Char(string="Formula Discount",related='promotion_id.formula_discount_string',help="สูตรสำหรับคำนวณส่วนลด")
    

    @api.onchange('product_id')
    def _onchange_product_id_promotion(self):
        # if not self.promotion_id:
        latest_promotion = self._get_latest_promotion(self.product_id)
        self.promotion_id = latest_promotion if latest_promotion else False

    def _get_latest_promotion(self, product):
        domain = [
            '&',
                '|',
                    '&', 
                        ('reward_type', '=', 'product'),
                        ('valid_product_ids', 'in', product.ids),
                    '&', '&',
                        ('reward_type', '=', 'discount'),
                        ('discount_apply_on', '=', 'specific_products'),
                        ('discount_specific_product_ids', 'in', product.ids),
                ('company_id', 'in', self.company_id.ids),
        ]
        return self.env['coupon.program'].search(domain, order="create_date desc", limit=1)

    @api.constrains('price_total')
    def _check_price_total(self):
        for line in self:
            if line.price_total < 0 and line.is_global_discount is False and line.is_reward_line is False:
                raise UserError('Net Amount cannot be negative. Please check the order lines.')
       
    @api.depends('triple_discount', 'product_uom_qty', 'price_unit', 'tax_id', 'dis_price','rounding_price','promotion_discount')
    def _compute_amount(self): # ใช้อันนี้แทน _compute_amount ของ hdc_sale_triple_discount แต่ไปใช้ใน hdc_sale_cancel_by_line แทน
        for line in self:
            total_dis = 0.0
            price_total = line.price_unit * line.product_uom_qty
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
                            total_baht = float(discount) 
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

            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)
            price_total = taxes['total_excluded']
            if line.tax_id:
                if line.tax_id.price_include:
                    price_total = taxes['total_included']

            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': price_total,
                'price_subtotal': taxes['total_excluded'],
                'dis_price': total_dis,
            })
                        
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['promotion_discount'] = self.promotion_discount
        return res