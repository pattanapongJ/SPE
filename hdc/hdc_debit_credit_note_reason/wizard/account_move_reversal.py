from odoo import models, fields, api, _
# from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"
    
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

    def reverse_moves(self):
        # Call original behavior
        action = super(AccountMoveReversal, self).reverse_moves()

        # Write the reason to new moves created from reverse
        for move in self.new_move_ids:
            move.debit_credit_note_reason_id = self.debit_credit_note_reason_id.id
            print(move , "move -------------------------------------------------------")

        return action
    
    # def reverse_moves(self):
    #     self.ensure_one()
    #     moves = self.move_ids

    #     # Create default values.
    #     default_values_list = []
    #     for move in moves:
    #         default_values_list.append(self._prepare_default_reversal(move))

    #     batches = [
    #         [self.env['account.move'], [], True],   # Moves to be cancelled by the reverses.
    #         [self.env['account.move'], [], False],  # Others.
    #     ]
    #     for move, default_vals in zip(moves, default_values_list):
    #         is_auto_post = bool(default_vals.get('auto_post'))
    #         is_cancel_needed = not is_auto_post and self.refund_method in ('cancel', 'modify')
    #         batch_index = 0 if is_cancel_needed else 1
    #         batches[batch_index][0] |= move
    #         batches[batch_index][1].append(default_vals)

    #     # Handle reverse method.
    #     moves_to_redirect = self.env['account.move']
    #     for moves, default_values_list, is_cancel_needed in batches:
    #         new_moves = moves._reverse_moves(default_values_list, cancel=is_cancel_needed)

    #         if self.refund_method == 'modify':
    #             moves_vals_list = []
    #             for move in moves.with_context(include_business_fields=True):
    #                 moves_vals_list.append(move.copy_data({'date': self.date if self.date_mode == 'custom' else move.date})[0])
    #             new_moves = self.env['account.move'].create(moves_vals_list)

    #         moves_to_redirect |= new_moves

    #     self.new_move_ids = moves_to_redirect
        
    #     for reverse_move in moves_to_redirect:
    #         for line in reverse_move.invoice_line_ids:
    #             account_id = self._get_computed_account(line).id if self._get_computed_account(line) else False
    #             if account_id:
    #                 line.update({'account_id': account_id or False})
                
    #     # Create action.
    #     action = {
    #         'name': _('Reverse Moves'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'account.move',
    #     }
    #     if len(moves_to_redirect) == 1:
    #         action.update({
    #             'view_mode': 'form',
    #             'res_id': moves_to_redirect.id,
    #             'context': {'default_move_type':  moves_to_redirect.move_type},
    #         })
    #     else:
    #         action.update({
    #             'view_mode': 'tree,form',
    #             'domain': [('id', 'in', moves_to_redirect.ids)],
    #         })
    #         if len(set(moves_to_redirect.mapped('move_type'))) == 1:
    #             action['context'] = {'default_move_type':  moves_to_redirect.mapped('move_type').pop()}
    #     return action