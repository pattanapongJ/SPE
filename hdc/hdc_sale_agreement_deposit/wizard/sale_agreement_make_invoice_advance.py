# Copyright 2019 Elico Corp, Dominique K. <dominique.k@elico-corp.com.sg>
# Copyright 2019 Ecosoft Co., Ltd., Kitti U. <kittiu@ecosoft.co.th>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class SaleAgreementAdvancePaymentInv(models.TransientModel):
    _name = "sale.agreement.advance.payment.inv"
    _description = "Sale Agreement Advance Payment Invoice"

    advance_payment_method = fields.Selection(
        [
            ("percentage", "Down payment (percentage)"),
            ("fixed", "Deposit payment (fixed amount)"),
        ],
        string="What do you want to invoice?",
        default="percentage",
        required=True,
    )
    sale_agreement_deposit_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Deposit Payment Product",
        domain=[("type", "=", "service")],
    )
    amount = fields.Float(
        string="Deposit Payment Amount",
        required=True,
        help="The amount to be invoiced in advance, taxes excluded.",
    )
    deposit_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Expense Account",
        domain=[("deprecated", "=", False)],
        help="Account used for deposits",
    )
    deposit_taxes_id = fields.Many2many(
        comodel_name="account.tax",
        string="Vendor Taxes",
        help="Taxes used for deposits",
    )

    @api.model
    def view_init(self, fields):
        active_id = self._context.get("active_id")
        sale_agreement = self.env["sale.blanket.order"].browse(active_id)
        # if sale_agreement.state != "done":
        #     raise UserError(_("This action is allowed only in Purchase Order sate"))
        return super().view_init(fields)

    @api.onchange("sale_agreement_deposit_product_id")
    def _onchagne_sale_agreement_deposit_product_id(self):
        product = self.sale_agreement_deposit_product_id
        if not product:
            product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
            product = self.env["product.product"].browse(int(product_id))
        self.deposit_account_id = product.property_account_expense_id
        self.deposit_taxes_id = product.supplier_taxes_id

    def _prepare_deposit_val(self, order, po_line, amount):
        ir_property_obj = self.env["ir.property"]
        account_id = False
        product = self.sale_agreement_deposit_product_id
        if not product:
            product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
            product = self.env["product.product"].browse(int(product_id))
        if product.id:
            account_id = (
                product.property_account_expense_id.id
                or product.categ_id.property_account_expense_categ_id.id
            )
        if not account_id:
            inc_acc = ir_property_obj._get(
                "property_account_expense_categ_id", "product.category"
            )
            account_id = (
                order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
            )
        if not account_id:
            raise UserError(
                _(
                    "There is no purchase account defined for this product: %s."
                    "\nYou may have to install a chart of account from "
                    "Accounting app, settings menu."
                )
                % (product.name,)
            )

        if self.amount <= 0:
            raise UserError(_("The value of the deposit must be positive."))
        context = {"lang": order.partner_id.lang}
        amount = self.amount
        if self.advance_payment_method == "percentage":  # Case percent
            if self.amount > 100:
                raise UserError(_("The percentage of the deposit must be not over 100"))
            amount = self.amount / 100 * (order.amount_before_discount - order.total_discount_amount_new)
        name = _("Down Payment")
        del context
        taxes = product.taxes_id.filtered(
            lambda r: not order.company_id or r.company_id == order.company_id
        )
        if order.fiscal_position_id and taxes:
            tax_ids = order.fiscal_position_id.map_tax(taxes).ids
        else:
            tax_ids = taxes.ids

        deposit_val = {
            "invoice_origin": order.name,
            "move_type": "out_invoice",
            "partner_id": order.partner_id.id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": name,
                        "account_id": account_id,
                        "price_unit": amount,
                        "quantity": 1.0,
                        "product_uom_id": product.uom_id.id,
                        "product_id": product.id,
                        "sale_agreement_line_id": po_line.id,
                        "tax_ids": [(6, 0, tax_ids)],
                        # "analytic_account_id": po_line.account_analytic_id.id or False,
                    },
                )
            ],
            "currency_id": order.currency_id.id,
            "invoice_payment_term_id": order.payment_term_id.id,
            "fiscal_position_id": order.fiscal_position_id.id
            or order.partner_id.property_account_position_id.id,
            "sale_agreement_id": order.id,
            "narration": order.note,
            "deposit_balance": amount,
            "transport_line_id": order.delivery_trl.id,
            "transport_desc":order.delivery_trl_description,
            "company_round_id": order.delivery_company.id,
            "company_round_desc": order.delivery_company_description,
            "invoice_user_employee_id":order.user_employee_id.id,
            "sale_spec_employee":order.sale_spec_employee.id,
            "sale_manager_employee_id":order.sale_manager_employee_id.id if order.sale_manager_employee_id else False,
            "user_sale_agreement_employee":order.administrator_employee.id,
            "department_id":order.department_id.id,
            "user_id":order.user_id.id,
            "sale_spec":order.sale_spec.id,
            "sale_manager_id":order.sale_manager_id.id if order.sale_manager_id else False,
            "sale_type_id":order.sale_type_id.id,
            "customer_po":order.customer_po,
            "modify_type_txt":order.modify_type_txt,
            "plan_home":order.plan_home,
            "room":order.room,
            "project_name":order.project_name.id if order.project_name else False,
            "finance_dimension_1_id":order.finance_dimension_1_id.id if order.finance_dimension_1_id else False,
            "finance_dimension_2_id":order.finance_dimension_2_id.id if order.finance_dimension_2_id else False,
            "finance_dimension_3_id":order.finance_dimension_3_id.id if order.finance_dimension_3_id else False,
            "billing_period_id":order.billing_period_id.id if order.billing_period_id else False,
            "billing_route_id":order.billing_route_id.id if order.billing_route_id else False,
            "billing_terms_id":order.billing_terms_id.id if order.billing_terms_id else False,
            "billing_place_id":order.billing_place_id.id if order.billing_place_id else False,
            "payment_period_id":order.payment_period_id.id if order.payment_period_id else False,
            "customer_ref":order.client_order_ref,
            "company_id":order.company_id.id
        }
        return deposit_val

    def _create_invoice(self, order, po_line, amount):
        Invoice = self.env["account.move"]
        deposit_val = self._prepare_deposit_val(order, po_line, amount)
        invoice = Invoice.create(deposit_val)
        invoice.message_post_with_view(
            "mail.message_origin_link",
            values={"self": invoice, "origin": order},
            subtype_id=self.env.ref("mail.mt_note").id,
        )
        return invoice

    def create_invoices(self):
        Saleagreement = self.env["sale.blanket.order"]
        IrDefault = self.env["ir.default"].sudo()
        sale_agreement = Saleagreement.browse(self._context.get("active_ids", []))
        # Create deposit product if necessary
        product = self.sale_agreement_deposit_product_id
        if not product:
            vals = self._prepare_deposit_product()
            product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
            product = self.env['product.product'].browse(int(product_id)).exists()
        BlanketLine = self.env["sale.blanket.order.line"]
        for order in sale_agreement:
            amount = self.amount
            if self.advance_payment_method == "percentage":  # Case percent
                amount = self.amount / 100 * (order.amount_before_discount - order.total_discount_amount_new)
            if product.type != "service":
                raise UserError(
                    _(
                        "The product used to invoice a down payment should be "
                        'of type "Service". Please use another product or '
                        "update this product."
                    )
                )
            taxes = product.supplier_taxes_id.filtered(
                lambda r: not order.company_id or r.company_id == order.company_id
            )
            if order.fiscal_position_id and taxes:
                tax_ids = order.fiscal_position_id.map_tax(taxes).ids
            else:
                tax_ids = taxes.ids
            context = {"lang": order.partner_id.lang}
            po_line = BlanketLine.create(
                {
                    "name": _("Advance: %s") % (time.strftime("%m %Y"),),
                    "price_unit": amount,
                    "original_uom_qty": 0.0,
                    "order_id": order.id,
                    "product_uom": product.uom_id.id,
                    "product_id": product.id,
                    "taxes_id": [(6, 0, tax_ids)],
                    "is_deposit": True,
                }
            )
            del context
            self._create_invoice(order, po_line, amount)
        if self._context.get("open_invoices", False):
            sale_agreement._reset_sequence()
            return sale_agreement.action_view_invoice()
        return {"type": "ir.actions.act_window_close"}

    def _prepare_deposit_product(self):
        return {
            "name": "Down Payment",
            "type": "service",
            "sale_agreement_method": "purchase",
            "property_account_expense_id": self.deposit_account_id.id,
            "supplier_taxes_id": [(6, 0, self.deposit_taxes_id.ids)],
            "company_id": False,
        }


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _default_deduct_downpayment(self):
        if self._context.get('active_ids', []):
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
            move_ids = self.env['account.move']
            for order in sale_orders:
                invoiceable_lines = order._get_invoiceable_lines(True)
                if invoiceable_lines.invoice_lines:
                    for line in invoiceable_lines.invoice_lines:
                        if line.move_id and line.move_id.deposit_balance > 0:
                            if line.move_id and any(sale_line.is_downpayment and not sale_line.is_deduct_downpayment for sale_line in line.sale_line_ids):
                                move_ids |= line.move_id
                if order.blanket_order_id:
                    move_ids |= order.blanket_order_id.invoice_ids.filtered(lambda l: l.deposit_balance > 0)
            
            return move_ids.ids
        else:
            return []
        
    def _create_invoice_deduct(self, so_line):
        if self.deposit_no and self.deduct_amount > 0:
            # ตรวจสอบว่าจำนวนเงินที่หักไม่เกินยอดคงเหลือในใบมัดจำ
            if self.deduct_amount > self.deposit_no.deposit_balance:
                raise UserError("Deduct amount cannot exceed the remaining deposit amount.")

            # เรียกฟังก์ชัน create_invoice_from_amount เพื่อสร้างใบแจ้งหนี้ด้วยยอดที่หัก
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
            order_lines = self.deposit_no.invoice_line_ids.mapped('sale_line_ids')
            sale_agreement_line_id = self.deposit_no.invoice_line_ids.mapped('sale_agreement_line_id')
            # if not order_lines:
            #     if not sale_agreement_line_id:
            #         raise UserError("No sale order lines found for the selected deposit.")
                # raise UserError("No sale order lines found for the selected deposit.")
            # deduct_data = {
            #     'name': _('Deduct Down Payment: %s') % (time.strftime('%m %Y'),),
            #     'price_unit': 0,
            #     'quantity': 0,
            #     'account_id': self.deposit_no.journal_id.default_account_id.id,  # บัญชีสำหรับมัดจำ
            #     'currency_id': self.currency_id.id,
            # }

            # invoices = sale_orders._create_invoices_deduct(False, deduct=deduct_data)
            invoices = sale_orders._create_invoices_deduct(False, deduct=False)

            if order_lines:
                self.env['sale.order.deposit.history'].create({
                    'sale_order_line_id': order_lines[0].id, 
                    'deposit_move_id': self.deposit_no.id,  
                    'deduct_move_id': invoices[0].id,  
                    'deducted_amount': self.deduct_amount,  
                })
            else:
                self.env['sale.blanket.deposit.order.history'].create({
                    'sale_agreement_line_id': sale_agreement_line_id[0].id, 
                    'deposit_move_id': self.deposit_no.id,  
                    'deduct_move_id': invoices[0].id,  
                    'deducted_amount': self.deduct_amount,  
                })

            # อัปเดตยอดคงเหลือของใบมัดจำ
            self.deposit_no._compute_deposit_balance()
        else:
            raise UserError("Please specify a valid deposit and deduction amount.")