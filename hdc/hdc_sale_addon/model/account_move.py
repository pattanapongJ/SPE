# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
import re

class AccountMove(models.Model):
    _inherit = "account.move"

    STATE_COLOR_MAPPING = {
        "draft": 3,
        "posted": 10,
        "cancel": 1,
    }

    color = fields.Integer(compute="_compute_color")

    amount_before_discount = fields.Float(string = "Amount Before Discount",
                                          compute = '_compute_amount_before_discount')

    global_discount = fields.Char(string = "Global Discount")
    global_discount_update = fields.Char()
    global_discount_total = fields.Float(string = "Global Discount Total", compute = '_compute_global_discount_total',
                                         store = True)
    
    total_discount_amount_new = fields.Float(string="Total Discount")

    @api.depends("state")
    def _compute_color(self):
        for rec in self:
            rec.color = self.STATE_COLOR_MAPPING.get(rec.state)

    @api.onchange('invoice_line_ids', 'invoice_line_ids.price_total')
    def _compute_amount_before_discount(self):
        for order in self:
            amount_untaxed = sum(line.price_total for line in order.invoice_line_ids if not line.product_id == order.env["product.product"].search([('name', '=', "Global Discount"), ('type', '=', "service")], limit=1))
            order.amount_before_discount = amount_untaxed

    @api.depends('global_discount','invoice_line_ids','invoice_line_ids.product_id')
    def _compute_global_discount_total(self):
        print('_compute_global_discount_total')
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
            else:
                order.global_discount_total = 0.0
            # for line in order.invoice_line_ids:
            #     if line.product_id == order.env["product.product"].search([('name', '=', "Global Discount"), ('type', '=', "service")], limit=1):
            #         line.price_unit = order.global_discount_total * -1
            #         line._onchange_price_subtotal()
                    
            order.total_discount_amount_new = order.global_discount_total

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    STATE_COLOR_MAPPING = {
        "draft": 3,
        "posted": 10,
        "cancel": 1,
    }

    color = fields.Integer(compute="_compute_color")

    @api.depends("move_id")
    def _compute_color(self):
        for rec in self:
            rec.color = self.STATE_COLOR_MAPPING.get(rec.move_id.state)
    
    @api.depends('ref', 'move_id')
    def name_get(self):
        result = []
        for line in self:
            name = line.move_id.name_get() or ''
            if line.ref:
                name += " (%s)" % line.ref
            #name += (line.name or line.product_id.display_name) and (' ' + (line.name or line.product_id.display_name)) or ''
            result.append((line.id, name[0][1]))
        return result