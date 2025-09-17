from odoo import api, models, _

class AccountPaymentDeduction(models.TransientModel):
    _inherit = 'account.payment.deduction'

    @api.onchange("open")
    def _onchange_open(self):
        if self.open:
            self.account_id = False
            self.name = _("Keep open")