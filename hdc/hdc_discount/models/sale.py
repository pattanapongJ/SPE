from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby
import re
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sales Order'

    customer_po = fields.Char(string="")
    sub_discount_amount = fields.Float(string="Sub Discount Amount", compute='_compute_sub_discount_amount')
    sub_discount_percentage = fields.Float(string="Sub Disc%", compute='_compute_sub_discount_amount')
    
    total_discount_amount = fields.Float(string="Total Discount%", compute='_compute_total_discount')
    total_discount_percentage = fields.Float(string="Total Discount Percentage", compute='_compute_total_discount')

    total_discount = fields.Float(string="Total Discount")
    amount_before_discount = fields.Float(string="Amount Before Discount", compute='_compute_amount_before_discount')
    total_discount_amount_new = fields.Float(string="Total Discount", compute='_compute_total_discount')
    
    @api.constrains('amount_total')
    def _check_amount_total(self):
        for line in self:
            if line.amount_total < 0 :
                raise UserError('Total is negative. Please check.')
    def recalculate_global_discount(self):
        return True

    def write(self, vals):
        #โค็ดสำหรับลบ line global_discount_line กรณีที่ มันโดนลบออกจาก sale order line
        if 'order_line' in vals:
            for line in vals['order_line']:
                if line[0] == 2:
                    global_discount_product = self.default_product_global_discount
                    # global_discount_product = self.env["product.product"].search([('name', '=', "Global Discount"), ('type', '=', "service")], limit=1)
                    check_global_discount_line = self.env["sale.order.line"].search([
                    ('id', '=', line[1])], limit=1)

                    if check_global_discount_line.product_id == global_discount_product:
                        self.global_discount = 0

        res = super().write(vals)

        return res

    # @api.onchange('order_line', 'order_line.price_unit', 'order_line.price_subtotal', 'order_line.triple_discount', 'global_discount', 'global_discount_total', 'write_date', 'order_line.product_uom_qty')
    # def _compute_amount_before_discount(self):
    #     for order in self:
    #         amount_untaxed = 0.0
    #         for line in order.order_line:
    #             if line.product_id != order.default_product_global_discount:
    #                 amount_untaxed += line.product_uom_qty * line.price_unit

    #         order.amount_before_discount = amount_untaxed
    @api.onchange('order_line', 'order_line.price_total')
    def _compute_amount_before_discount(self):
        for order in self:
            amount_untaxed = sum(line.price_total for line in order.order_line if not line.is_global_discount)
            order.amount_before_discount = amount_untaxed

    def _global_discount_total_line(self , gb):
        for order in self:
            amount_untaxed = 0.0
            for line in order.order_line:
                if line.product_id != order.default_product_global_discount:
                    amount_untaxed += line.price_subtotal

            global_discount_total = 0.0

            if gb:
                try:

                    global_discount_discounts = gb.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                    for discount in global_discount_discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for discount in global_discount_discounts:
                        if discount.endswith("%"):
                            dis_percen = discount.replace("%", "")
                            discount_amount = ((amount_untaxed) * float(dis_percen)) / 100
                            amount_untaxed -= discount_amount
                            global_discount_total += discount_amount
                        else:
                            discount_amount = float(discount)
                            amount_untaxed -= discount_amount
                            global_discount_total += discount_amount
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))

                return global_discount_total

    
    @api.constrains('customer_po')
    def _check_customer_po_unique(self):
        for order in self:
            if order.customer_po:
                domain = [
                    ('customer_po', '=', order.customer_po),
                    ('partner_id', '=', order.partner_id.id),
                    ('id', '!=', order.id),  # Exclude the current order
                    ('is_from_agreement', '=', False),
                ]
                duplicate_orders = self.search(domain)
                if duplicate_orders:
                    raise ValidationError("Customer PO No must be unique.")
                
    @api.onchange('order_line','order_line.price_unit','order_line.price_subtotal','order_line.triple_discount', 'global_discount','global_discount_total','write_date','order_line.product_uom_qty')
    def _compute_sub_discount_amount(self):
        for order in self:
            sub_discount = 0.0
            percen_discount = 0.0
            total_std_price = 0.0            
            total_subtotal = 0.0
            for line in order.order_line:
                if line.product_id and line.product_id.lst_price > 0 and line.product_uom_qty > 0:
                    std_price = line.product_id.lst_price
                    if line.product_id.uom_id:
                        new_qty = line.product_uom._compute_quantity(
                            line.product_uom_qty, line.product_id.uom_id
                        )
                    else:
                        new_qty = line.product_uom_qty
                    #หาผลรวมของ public price * product uom qty * factor
                    # total_std_price += std_price * line.product_uom_qty * ratio
                    total_std_price += std_price * new_qty
                                        
                    #หา price subtotal
                    total_subtotal += line.price_total
                    # total_subtotal += line.price_subtotal
                                        
            sub_discount = total_std_price - total_subtotal
            if total_std_price != 0:
                percen_discount = ((total_std_price - total_subtotal) * 100 / total_std_price)
            
            if sub_discount < 0 or percen_discount < 0:
                order.sub_discount_amount = 0.0
                order.sub_discount_percentage = 0.0
            else:
                order.sub_discount_amount = sub_discount
                order.sub_discount_percentage = percen_discount 
            
    @api.onchange('order_line','order_line.price_unit','order_line.price_subtotal','order_line.triple_discount', 'global_discount','global_discount_total','write_date','order_line.product_uom_qty')
    def _compute_total_discount(self):
        for order in self:
            total_discount = 0.0
            total_percen_discount = 0.0
            total_std_price = 0.0
            total_subtotal = 0.0
            
            for line in order.order_line:
                if line.product_id and line.product_id.lst_price > 0 and line.product_uom_qty > 0:
                    std_price = line.product_id.lst_price
                    line_price_subtotal = line.price_subtotal
                    line_sub_discount = order.sub_discount_amount
                    
                    if line.product_id.uom_id:
                        new_qty = line.product_uom._compute_quantity(
                            line.product_uom_qty, line.product_id.uom_id
                        )
                    else:
                        new_qty = line.product_uom_qty
 
                    #หาผลรวมของ public price * product uom qty * factor
                    total_std_price += std_price * new_qty
                    # total_std_price += std_price * line.product_uom_qty * ratio
                    
                    #หา price subtotal
                    total_subtotal += line.price_total
                    # total_subtotal += line.price_subtotal

            total_discount = (((total_std_price) - (total_subtotal) + order.global_discount_total))
            
            if total_std_price != 0:
                total_percen_discount = (((total_std_price) - (total_subtotal) + order.global_discount_total) * 100 / total_std_price)
            
            if total_discount < 0 or total_percen_discount < 0:
                order.total_discount_amount = 0.0
                order.total_discount_percentage = 0.0
            else:
                order.total_discount_amount = total_discount
                order.total_discount_percentage = total_percen_discount 
            order.total_discount_amount_new = order.global_discount_total
   
    @api.depends('global_discount','global_discount_update','order_line','order_line.product_id')
    def _compute_global_discount_total(self):
        for order in self:
            global_discount_total = 0.0
            order._compute_amount_before_discount()
            if order.global_discount:
                try:
                    global_discount_discounts = order.global_discount.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                    for discount in global_discount_discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for discount in global_discount_discounts:
                        if discount.endswith("%"):
                            dis_percen = discount.replace("%", "")
                            discount_amount = ((order.amount_before_discount) * float(dis_percen)) / 100
                            global_discount_total += discount_amount
                        else:
                            discount_amount = float(discount)
                            global_discount_total += discount_amount
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))
                order.global_discount_total = global_discount_total
                order.global_discount_update = global_discount_total
            else:
                order.global_discount_total = 0.0

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sales Order Line'
    
    bns_code = fields.Char(string="BNS Code")
    description_sale = fields.Char(string="Description Sale")
    is_global_discount = fields.Boolean('is global discount',default=False)

    @api.constrains('price_total')
    def _check_price_total(self):
        for line in self:
            if line.price_total < 0 and line.is_global_discount is False and line.is_reward_line is False: #แก้ให้ข้ามถ้าติดลบเพราะ promotion
                raise UserError('Net Amount cannot be negative. Please check the order lines.')
       
    @api.depends('triple_discount','price_subtotal','price_total','price_unit','product_id','order_id.global_discount','order_id.global_discount_total')
    def _compute_sub_discount_line(self):
        for line in self:
            if line.price_unit <= 0:
                line.sub_discount = 0.0
            else:
                std_price = line.product_id.lst_price
                if line.product_id.uom_id:
                    new_qty = line.product_uom._compute_quantity(
                        line.product_uom_qty, line.product_id.uom_id
                    )
                else:
                    new_qty = line.product_uom_qty
                cost = std_price * new_qty
                if cost == 0:
                    line.sub_discount = 0.0
                else:
                    sub_dis = ((cost) - line.price_total) * 100 / (cost)
                    if sub_dis <= 0:
                        line.sub_discount = 0.0
                    else:
                        line.sub_discount = sub_dis
            
    
    sub_discount = fields.Float(string="Sub Disc %", compute='_compute_sub_discount_line')   
    # sub_discount = fields.Float(string="Sub Disc %")   

    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.bns_code = self.product_id.bns_code
    
    @api.onchange('bns_code')
    def _compute_check_bns_code(self):
        bns_code_check = self.env["product.template"].search([('bns_code', '=', self.bns_code)], limit=1)
        if self.bns_code:
            if bns_code_check.bns_code == self.bns_code:
                self.product_id = bns_code_check.product_variant_id.id
            else:
                pass
                            
