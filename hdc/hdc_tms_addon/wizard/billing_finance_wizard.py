from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class BillingFinanceWizard(models.TransientModel):
    _inherit = "wizard.billing.finance"

    billing_finance = fields.Selection(
        selection_add=[("close", "ปิดใบวางบิล")],
        ondelete={
            'to_finance': 'cascade',
            'to_billing': 'cascade',
            'close': 'cascade',
        })


    def send_action(self):
        for line in self.invoice_line_ids:
            line.billing_status = self.billing_finance
            line.finance_type = False
            if self.billing_finance == 'to_finance':
                line.finance_type = self.finance_type
