from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class BillingFinanceWizard(models.TransientModel):
    _name = "wizard.billing.finance"
    _description = "Billing Finance Wizard"

    distribition_id = fields.Many2one('distribition.delivery.note',string="Delivery Slip", required=True, copy=False)
    issue_date = fields.Date(string="Issue Date", default=lambda self: fields.Date.today(), required=True)
    billing_finance = fields.Selection([
        ('to_finance', 'รอส่งห้องการเงิน'),
        ('to_billing', 'รอส่งให้ห้องวางบิล'),
    ], string="Billing / Finance", required=True)
    invoice_line_ids = fields.Many2many('distribition.invoice.line',string="Invoice Lines")
    finance_type = fields.Selection([
        ('cash', 'เงินสด/โอน/เช็ค'),
        ('urgent', 'ด่วนการเงิน'),
    ], string="Finance Type")

    def send_action(self):
        for line in self.invoice_line_ids:
            line.billing_status = self.billing_finance
            if self.billing_finance == 'to_finance':
                line.invoice_id.finance_type = self.finance_type
