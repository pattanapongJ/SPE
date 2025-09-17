from odoo import api, fields, models


class AccountMoveTaxInvoice(models.Model):
    _inherit = "account.move.tax.invoice"

    @api.model
    def create(self, values):
        res = super(AccountMoveTaxInvoice, self).create(values)
        if res:
            res.update(
                {
                    "tax_invoice_number": res.move_id.ref,
                    "tax_invoice_date": res.move_id.invoice_date,
                }
            )
        return res


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("invoice_date", "ref")
    def onchange_date_and_ref(self):
        for tax_inv in self.tax_invoice_ids:
            tax_inv.tax_invoice_number = self.ref
            tax_inv.tax_invoice_date = self.invoice_date

    def _post(self, soft=True):
        if not self.env.context.get(
                "check_purchase_tax_cash_basic"
        ) and not self.env.context.get("from_payment"):
            return super()._post(soft)
        for move in self:
            for tax_invoice in move.tax_invoice_ids.filtered(
                    lambda l: l.tax_line_id.type_tax_use == "purchase"
                              or (
                                      l.move_id.move_type == "entry"
                                      and not l.payment_id
                                      and l.move_id.journal_id.type != "sale"
                              )
            ):
                ## To Skip Automatic Post Tax Cash Basis for Purchase when Defer Posting is set False
                if tax_invoice.payment_id and not tax_invoice.allow_defer_posting():
                    tax_invoice.payment_id.write({"to_clear_tax": False})
                    return self.browse()
        return super()._post(soft)


class AccountRegisterPayment(models.TransientModel):
    _inherit = "account.payment.register"

    def _post_payments(self, to_process, edit_mode=False):
        self = self.with_context(check_purchase_tax_cash_basic=True)
        return super(AccountRegisterPayment, self)._post_payments(to_process, edit_mode)
