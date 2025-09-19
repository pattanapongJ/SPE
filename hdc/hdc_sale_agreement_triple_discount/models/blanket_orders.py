# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from collections import defaultdict
import re
class BlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    triple_discount = fields.Char('Discount')

    # @api.constrains('price_subtotal')
    # def _check_price_subtotal(self):
    #     for line in self:
    #         if line.price_subtotal < 0:
    #             raise UserError('Subtotal cannot be negative. Please check the order lines.')

    @api.depends("triple_discount","original_uom_qty", "price_unit", "taxes_id", "order_id.partner_id", "product_id", "currency_id", )
    def _compute_amount(self):
        for line in self:
            total_dis = 0.0
            price_total = (line.price_unit*line.original_uom_qty)
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
                            total_percen = ((price_total)*float(dis_percen))/100
                            price_total -= total_percen
                            total_dis += total_percen
                        else:
                            total_baht = float(discount)
                            price_total -= total_baht
                            total_dis += total_baht
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))

            price = (line.price_unit * line.original_uom_qty) - total_dis
            taxes = line.taxes_id.compute_all(price, line.currency_id, 1, product = line.product_id,
                partner = line.order_id.partner_id, )
            line.update({
                "price_tax": sum(t.get("amount", 0.0) for t in taxes.get("taxes", [])),
                "price_total": taxes["total_included"], "price_subtotal": taxes["total_excluded"],
                })


class BlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    def _prepare_so_line_vals(self, line):
        return {
            "product_id": line.product_id.id,
            "name": line.product_id.name,
            "product_uom": line.product_uom.id,
            "sequence": line.blanket_line_id.sequence,
            "price_unit": line.blanket_line_id.price_unit,
            "blanket_order_line": line.blanket_line_id.id,
            "product_uom_qty": line.qty,
            "triple_discount": line.triple_discount,
            "tax_id": [(6, 0, line.taxes_id.ids)],
            "analytic_tag_ids": [(6, 0, line.blanket_line_id.analytic_tag_ids.ids)],
        }

    # @api.model
    # def _default_lines(self):
    #     blanket_order_line_obj = self.env["sale.blanket.order.line"]
    #     blanket_order_line_ids = self.env.context.get("active_ids", False)
    #     active_model = self.env.context.get("active_model", False)
    #     blanket_order_id = self.env.context.get("default_blanket_order_id", False)
        
    #     if blanket_order_id:
    #         blanket_order = self.env["sale.blanket.order"].browse(blanket_order_id)
    #         bo_lines = blanket_order.line_ids
    #     else:

    #         if active_model == "sale.blanket.order":
    #             bo_lines = self._default_order().line_ids
    #         else:
    #             bo_lines = blanket_order_line_obj.browse(blanket_order_line_ids)

    #     self._check_valid_blanket_order_line(bo_lines)

    #     lines = [
    #         (
    #             0,
    #             0,
    #             {
    #                 "blanket_line_id": bol.id,
    #                 "product_id": bol.product_id.id,
    #                 "date_schedule": bol.date_schedule,
    #                 "remaining_uom_qty": bol.remaining_uom_qty,
    #                 "price_unit": bol.price_unit,
    #                 "triple_discount": bol.triple_discount,
    #                 "product_uom": bol.product_uom,
    #                 "qty": bol.remaining_uom_qty,
    #                 "partner_id": bol.partner_id,
    #             },
    #         )
    #         for bol in bo_lines.filtered(lambda l: l.remaining_uom_qty != 0.0 and l.is_deposit is False)
    #     ]
    #     return lines


    # def create_sale_order(self):
    #     order_lines_by_customer = defaultdict(list)
    #     currency_id = 0
    #     pricelist_id = 0
    #     user_id = 0
    #     payment_term_id = 0
    #     team_id = self.blanket_order_id.team_id.id
    #     sale_spec = self.blanket_order_id.sale_spec.id

    #     for line in self.line_ids.filtered(lambda l: l.qty != 0.0):
    #         if line.qty > line.remaining_uom_qty:
    #             raise UserError(_("You can't order more than the remaining quantities"))
    #         vals = self._prepare_so_line_vals(line)
    #         order_lines_by_customer[line.partner_id.id].append((0, 0, vals))

    #         if currency_id == 0:
    #             currency_id = line.blanket_line_id.order_id.currency_id.id
    #         elif currency_id != line.blanket_line_id.order_id.currency_id.id:
    #             currency_id = False

    #         if pricelist_id == 0:
    #             pricelist_id = line.blanket_line_id.pricelist_id.id
    #         elif pricelist_id != line.blanket_line_id.pricelist_id.id:
    #             pricelist_id = False

    #         if user_id == 0:
    #             user_id = line.blanket_line_id.user_id.id
    #         elif user_id != line.blanket_line_id.user_id.id:
    #             user_id = False

    #         if payment_term_id == 0:
    #             payment_term_id = line.blanket_line_id.payment_term_id.id
    #         elif payment_term_id != line.blanket_line_id.payment_term_id.id:
    #             payment_term_id = False

    #     if not order_lines_by_customer:
    #         raise UserError(_("An order can't be empty"))

    #     if not currency_id:
    #         raise UserError(
    #             _(
    #                 "Can not create Sale Order from Blanket "
    #                 "Order lines with different currencies"
    #             )
    #         )

    #     res = []
    #     for customer in order_lines_by_customer:
    #         order_vals = self._prepare_so_vals(
    #             customer,
    #             user_id,
    #             currency_id,
    #             pricelist_id,
    #             payment_term_id,
    #             order_lines_by_customer,
    #             team_id,
    #             sale_spec,
    #         )
    #         sale_order = self.env["sale.order"].create(order_vals)
    #         res.append(sale_order.id)
    #     return {
    #         "domain": [("id", "in", res)],
    #         "name": _("Sales Orders"),
    #         "view_type": "form",
    #         "view_mode": "tree,form",
    #         "res_model": "sale.order",
    #         "context": {"from_sale_order": True},
    #         "type": "ir.actions.act_window",
    #     }

    # line_ids = fields.One2many("sale.blanket.order.wizard.line", "wizard_id", string = "Lines",
    #     default = _default_lines, )

class BlanketOrderWizardLine(models.TransientModel):
    _inherit = "sale.blanket.order.wizard.line"

    triple_discount = fields.Char('Discount')