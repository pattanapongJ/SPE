from odoo import models, fields, api, _
# from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"
    
    fiscal_pos_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', compute='_compute_fiscal_position')
    
    @api.depends('journal_id')
    def _compute_fiscal_position(self):
        self.fiscal_pos_id = self.journal_id.fiscal_pos_id
        
    def _get_computed_account(self, line):
            self.ensure_one()

            if not line.product_id:
                return 
            
            fiscal_position = self.fiscal_pos_id
            accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
            if line.move_id.is_sale_document(include_receipts=True):
                # Out invoice.
                return accounts['income'] or line.account_id
            elif line.move_id.is_purchase_document(include_receipts=True):
                # In invoice.
                return accounts['expense'] or line.account_id
    
    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        
        res.update({
            'fiscal_position_id': self.fiscal_pos_id and self.fiscal_pos_id.id or move.fiscal_position_id.id,
            'invoice_line_ids': [],
        })
        
        for line in move.invoice_line_ids:
            account_id = self._get_computed_account(line).id if self._get_computed_account(line) else False

            line_vals = {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'tax_ids': [(6, 0, self.fiscal_pos_id.map_tax(line.tax_ids).ids if self.fiscal_pos_id else line.tax_ids.ids)],
                'account_id': account_id or False,
                'move_id': move.id,
            }
            res['invoice_line_ids'].append((0, 0, line_vals))
        
        return res
    
    
    def reverse_moves(self):
        self.ensure_one()
        moves = self.move_ids

        # Create default values.
        default_values_list = []
        for move in moves:
            default_values_list.append(self._prepare_default_reversal(move))

        batches = [
            [self.env['account.move'], [], True],   # Moves to be cancelled by the reverses.
            [self.env['account.move'], [], False],  # Others.
        ]
        for move, default_vals in zip(moves, default_values_list):
            is_auto_post = bool(default_vals.get('auto_post'))
            is_cancel_needed = not is_auto_post and self.refund_method in ('cancel', 'modify')
            batch_index = 0 if is_cancel_needed else 1
            batches[batch_index][0] |= move
            batches[batch_index][1].append(default_vals)

        # Handle reverse method.
        moves_to_redirect = self.env['account.move']
        for moves, default_values_list, is_cancel_needed in batches:
            new_moves = moves._reverse_moves(default_values_list, cancel=is_cancel_needed)

            if self.refund_method == 'modify':
                moves_vals_list = []
                for move in moves.with_context(include_business_fields=True):
                    moves_vals_list.append(move.copy_data({'date': self.date if self.date_mode == 'custom' else move.date})[0])
                new_moves = self.env['account.move'].create(moves_vals_list)

            moves_to_redirect |= new_moves

        self.new_move_ids = moves_to_redirect
        
        for reverse_move in moves_to_redirect:
            for line in reverse_move.invoice_line_ids:
                account_id = self._get_computed_account(line).id if self._get_computed_account(line) else False
                if account_id:
                    line.update({'account_id': account_id or False})
                
        # Create action.
        action = {
            'name': _('Reverse Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
        }
        if len(moves_to_redirect) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': moves_to_redirect.id,
                'context': {'default_move_type':  moves_to_redirect.move_type},
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', moves_to_redirect.ids)],
            })
            if len(set(moves_to_redirect.mapped('move_type'))) == 1:
                action['context'] = {'default_move_type':  moves_to_redirect.mapped('move_type').pop()}
        return action