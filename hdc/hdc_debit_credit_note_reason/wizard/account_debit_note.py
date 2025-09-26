from odoo import models, fields, api, _
# from odoo.exceptions import UserError


class AccountDebitNote(models.TransientModel):
    _inherit = "account.debit.note"
    
    debit_credit_note_reason_id = fields.Many2one('debit.credit.note.reason', string="Debit,Credit Note Reason")
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'debit_credit_note_reason_id' in fields:
            move_ids = self.env.context.get('active_ids')
            if move_ids and self.env.context.get('active_model') == 'account.move':
                moves = self.env['account.move'].browse(move_ids)
                reason = moves[:1].debit_credit_note_reason_id.id if moves else False
                res['debit_credit_note_reason_id'] = reason
        return res
    
    def _prepare_default_values(self, move):
        values = super()._prepare_default_values(move)
        if self.debit_credit_note_reason_id:
            values['debit_credit_note_reason_id'] = self.debit_credit_note_reason_id.id        
        return values
