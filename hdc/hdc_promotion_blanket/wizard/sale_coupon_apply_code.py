# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class SaleCouponApplyCode(models.TransientModel):
    _inherit = 'sale.coupon.apply.code'

    is_sale_blanket = fields.Boolean('is_sale_blanket')
    is_quotation = fields.Boolean('is_quotation')

    def process_coupon(self):
        model = self.env['sale.order']
        if self.is_sale_blanket:
            model = self.env['sale.blanket.order']
        if self.is_quotation:
            model = self.env['quotation.order']

        sales_order = model.browse(self.env.context.get('active_id'))
        error_status = self.apply_coupon(sales_order, self.coupon_code)
        if error_status.get('error', False):
            raise UserError(error_status.get('error', False))
        if error_status.get('not_found', False):
            raise UserError(error_status.get('not_found', False))
        
    def apply_coupon(self, order, coupon_code):
        error_status = {}
        program_domain = order._get_coupon_program_domain()
        program_domain = expression.AND([program_domain, [('promo_code', '=', coupon_code)]])
        program = self.env['coupon.program'].search(program_domain)
        if self.is_sale_blanket:
            line = order.line_ids
        elif self.is_quotation:
            line = order.quotation_line
        else:
            line = order.order_line
        if program:
            error_status = program._check_promo_code(order, coupon_code)
            if not error_status:
                if program.promo_applicability == 'on_next_order':
                    if program.discount_line_product_id.id not in order.generated_coupon_ids.filtered(lambda coupon: coupon.state in ['new', 'reserved']).mapped('discount_line_product_id').ids:
                        coupon = order._create_reward_coupon(program)
                        return {
                            'generated_coupon': {
                                'reward': coupon.program_id.discount_line_product_id.name,
                                'code': coupon.code,
                            }
                        }
                else:
                    order_line_count = len(line)
                    order._create_reward_line(program)
                    if self.is_sale_blanket:
                        line = order.line_ids
                    elif self.is_quotation:
                        line = order.quotation_line
                    else:
                        line = order.order_line
                    if order_line_count < len(line):
                        order.code_promo_program_id = program
        else:
            coupon = self.env['coupon.coupon'].search([('code', '=', coupon_code)], limit=1)
            if coupon:
                if self.is_sale_blanket:
                    error_status = coupon._check_coupon_code_blanket(order)
                if self.is_quotation:
                    error_status = coupon._check_coupon_code_quotation(order)
                else:
                    error_status = coupon._check_coupon_code(order)
                if not error_status:
                    # Consume coupon only if reward lines were created
                    order_line_count = len(line)
                    order._create_reward_line(coupon.program_id)
                    if self.is_sale_blanket:
                        line = order.line_ids
                    elif self.is_quotation:
                        line = order.quotation_line
                    else:
                        line = order.order_line
                    if order_line_count < len(line):
                        order.applied_coupon_ids += coupon
                        coupon.write({'state': 'used'})
            else:
                error_status = {'not_found': _('This coupon is invalid (%s).') % (coupon_code)}
        return error_status