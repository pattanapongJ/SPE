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

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    total_discount_price = fields.Float("ส่วนลดรวม Before Global Disc",compute='_compute_discount_price', tracking = True,digits='Product Price')
    discount_price = fields.Char("ส่วนลดท้ายบิล", tracking = True,digits='Product Price')

    total_before_global_disc = fields.Float(string="Total Before Global Disc", compute='_compute_discount_price',digits='Product Price')
    total_global_disc = fields.Float(string="Total Global Disc",compute='_compute_total_global_disc',digits='Product Price')

    # currency_id = fields.Many2one('res.currency', 'Currency', required = True,
    #                               domain = [('rate_type','=', 'sell')],
    #                               states = READONLY_STATES,
    #                               default = lambda self: self.env.company.currency_id.id)

    def _compute_discount_price(self):
        for rec in self:
            total_discount_price = 0
            total_before_global_disc = 0
            for line in rec.order_line:
                total_before_global_disc += line.total_before_global_disc
                if line.global_disc_status:
                    total_discount_price += line.total_before_global_disc

            rec.total_discount_price = total_discount_price
            rec.total_before_global_disc = total_before_global_disc

    def _compute_discount_amount(self):
        self.ensure_one()
        if self.discount_price:
            discount_str = self.discount_price.strip()
            if discount_str.endswith('%'):
                # If the discount is a percentage
                try:
                    percentage = float(discount_str[:-1])
                    return (self.amount_untaxed * percentage) / 100
                except:
                    raise UserError("ส่วนลดไม่ถูกต้อง กรุณาใส่ตัวเลขหรือตัวเลขตามด้วย '%' เช่น 10%")
            else:
                # If the discount is a fixed amount
                try:
                    return float(discount_str)
                except:
                    raise UserError("ส่วนลดไม่ถูกต้อง กรุณาใส่ตัวเลขหรือตัวเลขตามด้วย '%' เช่น 10%")
        return 0.0
    
    def _compute_total_before_global_disc_true(self):
        total_before_global_disc_true = 0
        for line in self.order_line:
            if line.global_disc_status:
                total_before_global_disc_true += line.total_before_global_disc

        return total_before_global_disc_true
    
    def _compute_total_global_disc(self):
        for rec in self:
            total_global_disc = 0
            for line in rec.order_line:
                line.cal_global_disc_amt()
                total_global_disc += line.global_disc_amt

            rec.total_global_disc = total_global_disc

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    user_id = fields.Many2one('res.users', related='order_id.user_id', string='Purchase Representative', store=True)

    gross_unit_price = fields.Float(string = "Gross Unit Price", required = True ,digits='Product Price',default=0)
    multi_disc = fields.Char('Multi Disc.', default = '0')
    multi_disc_amount = fields.Float(string = "Multi Disc Amount",compute='_compute_multi_disc_amount', store = True,digits='Product Price')
    total_before_global_disc = fields.Float(string = "Total Before Global Disc",compute='_compute_multi_disc_amount', digits='Product Price')
    global_disc_amt = fields.Float(string = "Global Disc Amt", digits='Product Price')
    global_disc_status = fields.Boolean(string = "Global Disc Status", default=True, store=True)

    @api.constrains('price_total')
    def _check_price_total(self):
        for line in self:
            if line.price_total < 0:
                raise UserError('Net Amount cannot be negative. Please check the order lines.')
            
    @api.onchange("product_id")
    def _check_type_product(self):
        if self.product_id.type == "service":
            self.global_disc_status = False
            return
        self.global_disc_status = True

    @api.depends("gross_unit_price", "price_unit", "multi_disc","global_disc_status")
    def _compute_multi_disc_amount(self):
        for rec in self:
            price_total = (rec.gross_unit_price*rec.product_qty)
            total_dis = 0.0
            if rec.multi_disc:
                try:
                    discounts = rec.multi_disc.replace(" ", "").split("+")
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
            rec.multi_disc_amount = total_dis
            total_before_global_disc = (rec.gross_unit_price*rec.product_qty) - total_dis
            rec.total_before_global_disc = total_before_global_disc

    def cal_global_disc_amt(self):
        for rec in self:
            # Calculate the total discount amount
            total_discount_amount = float(rec.order_id._compute_discount_amount())   
            total_before_global_disc_true = float(rec.order_id._compute_total_before_global_disc_true())
                 
            discount_global_line = 0
            if rec.order_id.discount_price and rec.global_disc_status:
                discount_str = rec.order_id.discount_price.strip()
                if discount_str.endswith('%'):
                    percentage = float(discount_str[:-1])
                    discount_global_line = (rec.total_before_global_disc * percentage) / 100
                else:
                    discount_global_price = float(discount_str)
                    discount_global_line = (rec.total_before_global_disc/total_before_global_disc_true) * discount_global_price  

            rec.global_disc_amt = discount_global_line
            if rec.product_qty == 0:
                rec.price_unit = 0
            else:
                # Adjust the price_unit based on the calculated discount
                rec.price_unit = ((rec.product_qty * rec.gross_unit_price) - rec.multi_disc_amount - rec.global_disc_amt) / rec.product_qty
    #แบบเก่า
    # def cal_global_disc_amt(self):
    #     for rec in self:
    #         if rec.order_id.discount_price != 0 and rec.order_id.total_discount_price != 0:
    #             if rec.global_disc_status:
    #                 global_disc_amt = rec.order_id.discount_price* rec.total_before_global_disc / rec.order_id.total_discount_price
    #             else:
    #                 global_disc_amt = 0 * rec.total_before_global_disc / rec.order_id.total_discount_price
    #         else:
    #             global_disc_amt = 0
    #         if rec.global_disc_status:
    #             rec.global_disc_amt = global_disc_amt
    #         if rec.product_qty == 0:
    #             rec.price_unit = 0
    #         else:
    #             rec.price_unit = ((rec.product_qty * rec.gross_unit_price) - rec.multi_disc_amount - rec.global_disc_amt) / rec.product_qty
    
    def _prepare_account_move_line(self, move=False):
        result = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)
        result['gross_unit_price'] = self.gross_unit_price

        return result