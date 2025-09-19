from odoo import models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _synchronize_from_moves(self, changed_fields):
        if any(payment.state == 'posted' for payment in self):
            self = self.with_context(skip_account_move_synchronization=True)
        super(AccountPayment, self)._synchronize_from_moves(changed_fields)
