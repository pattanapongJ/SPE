from odoo import api, fields, models


class AccountMoveTaxInvoice(models.Model):
    _inherit = "account.move.tax.invoice"

    # vat = fields.Char(string="Tax ID", compute="_compute_invoice_line_tax_id", store=True)
    # branch = fields.Char(string="Tax Branch", compute="_compute_invoice_line_tax_id", store=True)

    def allow_defer_posting(self):
        if self.env.context.get("draft_payment_include_tax_invoice"):
            return True
        return self.company_id.allow_defer_posting and self.move_state == "draft"

    # @api.depends('partner_id')
    # def _compute_invoice_line_tax_id(self):
    #     for p in self:
    #         if p.partner_id:
    #             p.vat = p.partner_id.vat
    #             p.branch = p.partner_id.branch
