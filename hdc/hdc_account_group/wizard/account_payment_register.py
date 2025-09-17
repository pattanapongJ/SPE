from odoo import api, fields, models

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    
    def _init_payments(self, to_process, edit_mode=False):
        payments = super()._init_payments(to_process, edit_mode)

        account_totals = {}
        for line in payments.move_id.line_ids:
            account_id = line.account_id.id
            if account_id not in account_totals:
                account_totals[account_id] = {
                    'debit': 0.0,
                    'credit': 0.0,
                    'name': line.name
                }
            
            account_totals[account_id]['debit'] += line.debit
            account_totals[account_id]['credit'] += line.credit
        
        account_lines = []
        for account_id, totals in account_totals.items():
            account_lines.append((0, 0, {
                'invoice_group_account_account_id': account_id,
                'invoice_group_account_label': totals['name'],
                'invoice_group_account_debit': totals['debit'],
                'invoice_group_account_credit': totals['credit'],
            }))
        
        if account_lines:
            payments.move_id.invoice_group_account_line_ids = [(5, 0, 0)] + account_lines
        
        return payments