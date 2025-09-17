from odoo import fields, models


class PartialPaymentWizard(models.TransientModel):
    _inherit = "partial.payment.wizard"

    def _default_due_amount(self):
        move = self.env['account.move'].browse(self.env.context.get('move_id'))
        move_residual = abs(move.amount_residual)
        outstanding_amount = self._default_outstanding_amount()
        return move_residual if outstanding_amount > move_residual else outstanding_amount

    partial_amount = fields.Float(string='Amount to Pay', required=True,default=_default_due_amount)

    reconcile_date = fields.Date(string='Reconcile Date', default=fields.Date.context_today)




    def _create_partial_reconcile(self):
        record = super(PartialPaymentWizard, self)._create_partial_reconcile()
        record.write({
            'reconcile_date': self.reconcile_date
        })
        return record
