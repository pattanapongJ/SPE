from odoo import models, fields, api, _
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_payments_widget_to_reconcile_info(self):
        # Call the original method first to keep existing logic
        super(AccountMove, self)._compute_payments_widget_to_reconcile_info()

        for move in self:
            payments_widget_vals = json.loads(move.invoice_outstanding_credits_debits_widget)
            if payments_widget_vals:
                # Add the new key-value to the 'content' list
                for content_item in payments_widget_vals.get('content', []):
                    line = self.env['account.move.line'].browse(content_item['id'])
                    # Add 'account_id' to the content
                    content_item['move_name'] = line.move_name

                # Update the widget with the new content
                move.invoice_outstanding_credits_debits_widget = json.dumps(payments_widget_vals)
