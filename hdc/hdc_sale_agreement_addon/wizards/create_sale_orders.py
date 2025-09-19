# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class BlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    def _prepare_so_vals(
        self,
        customer,
        user_id,
        currency_id,
        pricelist_id,
        payment_term_id,
        order_lines_by_customer,
        
    ):
        vals = super()._prepare_so_vals(customer,user_id,currency_id,pricelist_id,payment_term_id,order_lines_by_customer)
        vals.update({
            "customer_po": self.blanket_order_id.customer_po,
            "po_date": self.blanket_order_id.po_date,
            "expire_date":self.blanket_order_id.expire_date,
            "customer_contact_date":self.blanket_order_id.customer_contact_date,
            "client_order_ref":self.blanket_order_id.client_order_ref,
            "priority":self.blanket_order_id.priority,
            "warehouse_id":self.blanket_order_id.warehouse_id.id,
            "contact_person":self.blanket_order_id.contact_person.id,
            "validity_date":self.blanket_order_id.validity_date,
            "modify_type_txt":self.blanket_order_id.modify_type_txt,
            "type_id":self.blanket_order_id.sale_type_id.id,
            "plan_home":self.blanket_order_id.plan_home,
            "fiscal_position_id":self.blanket_order_id.fiscal_position_id.id,
            "user_sale_agreement":self.blanket_order_id.administrator.id,
            "sale_manager_id":self.blanket_order_id.sale_manager_id.id,
            "remark": self.blanket_order_id.remark,
            "requested_ship_date":self.blanket_order_id.requested_ship_date,
            "requested_receipt_date":self.blanket_order_id.requested_receipt_date,
            "delivery_trl": self.blanket_order_id.delivery_trl.id,
            "delivery_trl_description": self.blanket_order_id.delivery_trl_description,
            "delivery_company": self.blanket_order_id.delivery_company.id,
            "delivery_company_description": self.blanket_order_id.delivery_company_description,
            "days_delivery": self.blanket_order_id.days_delivery,
            "global_discount": self.blanket_order_id.global_discount,
            "payment_method_id": self.blanket_order_id.payment_method_id.id,
            "billing_period_id": self.blanket_order_id.billing_period_id.id,
            "billing_route_id": self.blanket_order_id.billing_route_id.id,
            "billing_place_id": self.blanket_order_id.billing_place_id.id,
            "billing_terms_id": self.blanket_order_id.billing_terms_id.id,
            "payment_period_id": self.blanket_order_id.payment_period_id.id,
            "is_from_agreement": True,
            "branch_id": self.blanket_order_id.branch_id.id,
        })
        return vals
    
    def _prepare_so_line_vals(self, line):
        return {
            "product_id": line.selected_product_id.id,
            "name": line.selected_product_id.name,
            "product_uom": line.product_uom.id,
            "sequence": line.blanket_line_id.sequence,
            "price_unit": line.blanket_line_id.price_unit,
            "blanket_order_line": line.blanket_line_id.id,
            "product_uom_qty": line.qty,
            "tax_id": [(6, 0, line.taxes_id.ids)],
            "analytic_tag_ids": [(6, 0, line.blanket_line_id.analytic_tag_ids.ids)],
            "sequence2":line.blanket_line_id.sequence2,
            "display_type":line.blanket_line_id.display_type,
            "pick_location_id":line.blanket_line_id.pick_location_id.id,
            "warehouse_id":line.blanket_line_id.warehouse_id.id,
            # "finance_dimension_1_id":line.blanket_line_id.finance_dimension_1_id.id,
            # "finance_dimension_2_id":line.blanket_line_id.finance_dimension_2_id.id,
            "discount":line.blanket_line_id.discount,
            "triple_discount":line.blanket_line_id.triple_discount,
            "rounding_price":line.blanket_line_id.rounding_price,
            "note":line.blanket_line_id.note,
            "barcode":line.blanket_line_id.barcode,
            "currency_id":line.blanket_line_id.currency_id.id,
            "company_id":line.blanket_line_id.company_id.id,
            "is_global_discount":line.blanket_line_id.is_global_discount,

        }

    def check_over_remain(self):
        lang = self.env.user.lang or "en_US"
        warning_msg = (
            "กรุณาตรวจสอบยอดการเปิด SO เนื่องจากจำนวนที่ท่านเปิดเกินกว่าที่ทำสัญญาขาย Sale Agreement"
            if lang == "th_TH"
            else "Please check the SO opening amount as it exceeds the quantity specified in the Sale agreement."
        )
        return {
            "name": _("Warning"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "sale.blanket.order.warning.wizard",
            "target": "new",
            "context": {
                "default_message": warning_msg,
                "default_wizard_id": self.id,
                "default_lang": lang,
            },
        }
    
    def create_sale_order(self,allow_exceed=False):
        order_lines_by_customer = defaultdict(list)
        currency_id = 0
        pricelist_id = 0
        user_id = 0
        payment_term_id = 0
        for line in self.line_ids.filtered(lambda l: l.qty != 0.0):
            # return_qty = line.blanket_line_id.return_qty
            remain = line.remaining_uom_qty
            check_over_qty = False
            # order_qty = line.qty
            order_qty = sum(self.line_ids.filtered(lambda l: l.blanket_line_id == line.blanket_line_id).mapped("qty"))

            if order_qty > remain :
                check_over_qty = True                   
            if check_over_qty and not allow_exceed:
                return self.check_over_remain()
            # if line.secondary_uom_qty > line.remaining_uom_qty:
            #     raise UserError(_("You can't order more than the remaining quantities"))

            # if return_qty :
            #     if return_qty <= order_qty:
            #         return_qty = 0.0
            #     else:
            #         return_qty -= order_qty

            vals = self._prepare_so_line_vals(line)
            vals.update({
                "external_customer": line.blanket_line_id.external_customer.id if line.blanket_line_id.external_customer else False,
                "external_item": line.blanket_line_id.external_item,
                "barcode_customer": line.blanket_line_id.barcode_customer,
                "barcode_modern_trade": line.blanket_line_id.barcode_modern_trade,
                "description_customer": line.blanket_line_id.description_customer,
                "modify_type_txt": line.blanket_line_id.modify_type_txt,
                "plan_home": line.blanket_line_id.plan_home,
                "room": line.blanket_line_id.room,
            })

            order_lines_by_customer[line.partner_id.id].append((0, 0, vals))

            if currency_id == 0:
                currency_id = line.blanket_line_id.order_id.currency_id.id
            elif currency_id != line.blanket_line_id.order_id.currency_id.id:
                currency_id = False

            if pricelist_id == 0:
                pricelist_id = line.blanket_line_id.pricelist_id.id
            elif pricelist_id != line.blanket_line_id.pricelist_id.id:
                pricelist_id = False

            if user_id == 0:
                user_id = line.blanket_line_id.user_id.id
            elif user_id != line.blanket_line_id.user_id.id:
                user_id = False

            if payment_term_id == 0:
                payment_term_id = line.blanket_line_id.payment_term_id.id
            elif payment_term_id != line.blanket_line_id.payment_term_id.id:
                payment_term_id = False

        if not order_lines_by_customer:
            raise UserError(_("An order can't be empty"))

        if not currency_id:
            raise UserError(
                _(
                    "Can not create Sale Order from Blanket "
                    "Order lines with different currencies"
                )
            )

        res = []
        for customer in order_lines_by_customer:
            order_vals = self._prepare_so_vals(
                customer,
                user_id,
                currency_id,
                pricelist_id,
                payment_term_id,
                order_lines_by_customer,
            )
            sale_order = self.env["sale.order"].create(order_vals)
            res.append(sale_order.id)
        return {
            "domain": [("id", "in", res)],
            "name": _("Sales Orders"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "context": {"from_sale_order": True},
            "type": "ir.actions.act_window",
        }
    
    @api.model
    def _default_lines(self):
        blanket_order_line_obj = self.env["sale.blanket.order.line"]
        blanket_order_line_ids = self.env.context.get("active_ids", False)
        active_model = self.env.context.get("active_model", False)
        blanket_order_id = self.env.context.get("default_blanket_order_id", False)
        
        if blanket_order_id:
            blanket_order = self.env["sale.blanket.order"].browse(blanket_order_id)
            bo_lines = blanket_order.line_ids
        else:

            if active_model == "sale.blanket.order":
                bo_lines = self._default_order().line_ids
            else:
                bo_lines = blanket_order_line_obj.browse(blanket_order_line_ids)

        self._check_valid_blanket_order_line(bo_lines)

        lines = [
            (
                0,
                0,
                {
                    "blanket_line_id": bol.id,
                    "product_id": bol.product_id.id,
                    "selected_product_id": bol.product_id.id,
                    "date_schedule": bol.date_schedule,
                    "remaining_uom_qty": bol.remaining_uom_qty,
                    "price_unit": bol.price_unit,
                    "triple_discount": bol.triple_discount,
                    "product_uom": bol.product_uom,
                    "qty": bol.remaining_uom_qty,
                    "partner_id": bol.partner_id,
                },
            )
            for bol in bo_lines.filtered(lambda l: l.remaining_uom_qty != 0.0 and l.is_deposit is False)
        ]
        return lines
    line_ids = fields.One2many("sale.blanket.order.wizard.line", "wizard_id", string = "Lines",
        default = _default_lines, )

class BlanketOrderWizardLine(models.TransientModel):
    _inherit = "sale.blanket.order.wizard.line"

    alternative_ids_m2m = fields.Many2many(related='product_id.alternative_ids_m2m', string="Alternatives Products")
    selected_product_id = fields.Many2one("product.product",string="Product SO",domain="['|',('id', 'in', alternative_ids_m2m),('id', '=', product_id)]" )
    categ_id = fields.Many2one(related='product_id.categ_id', string='category')
    modify_type_txt = fields.Char(string="แปลง/Type/Block", related="blanket_line_id.modify_type_txt") 
    plan_home = fields.Char(string="แบบบ้าน", related="blanket_line_id.plan_home")
    room = fields.Char(string="ชั้น/ห้อง", related="blanket_line_id.room")
    external_customer = fields.Many2one('res.partner', string="External Customer",domain=[('customer','=',True)], related="blanket_line_id.external_customer")
    external_item = fields.Char(string="External Item", related="blanket_line_id.external_item")
    barcode_customer = fields.Char(string="Barcode Customer", related="blanket_line_id.barcode_customer")
    barcode_modern_trade = fields.Char(string="Barcode Product", related="blanket_line_id.barcode_modern_trade")
    description_customer = fields.Text(string="External Description", related="blanket_line_id.description_customer")
    
    # @api.onchange('product_id', 'selected_product_id')
    # def _onchange_selected_product_domain(self):
    #     if self.product_id:
    #         if self.alternative_ids_m2m:
    #             domain = ['|',('id', 'in', self.alternative_ids_m2m.ids),('id', '=', self.product_id.id)]
    #         else:
    #             domain = [('categ_id', '=', self.categ_id.id)]
    #         return {'domain': {'selected_product_id': domain}}
    #     return {'domain': {'selected_product_id': []}}

class BlanketOrderWarningWizard(models.TransientModel):
    _name = "sale.blanket.order.warning.wizard"
    _description = "Sale Blanket Order Over Quantity Warning"

    message = fields.Text(string="Message", readonly=True)
    lang = fields.Char(string="lang", readonly=True)
    wizard_id = fields.Many2one("sale.blanket.order.wizard", string="Wizard", readonly=True)

    def action_confirm(self):
        return self.wizard_id.create_sale_order(allow_exceed=True)

    def action_cancel(self):
        action_ref = "sale_blanket_order.view_create_sale_order" 
        return {
            "name": _("Create Sale Order"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "sale.blanket.order.wizard",
            "target": "new",
            "res_id": self.wizard_id.id,
            "context": {
                "default_wizard_id": self.wizard_id.id,
            },
            "view_id": self.env.ref(f"{action_ref}").id,
        }