from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _create_exchange_difference_move(self):
        exchange_move = super(AccountMoveLine, self)._create_exchange_difference_move()
        if exchange_move and self._context.get('from_payment', False):
            exchange_move.line_ids.write({
                'finance_dimension_1_id': self._context.get('finance_dimension_1_id'),
                'finance_dimension_2_id': self._context.get('finance_dimension_2_id'),
                'finance_dimension_3_id': self._context.get('finance_dimension_3_id')
            })
        return exchange_move

    def write(self, vals):
        if self._check_dimenstion_update(vals) and 'posted' in self.mapped('parent_state'):
            return super(AccountMoveLine, self.with_context(skip_account_move_synchronization=True)).write(vals)
        return super(AccountMoveLine, self).write(vals)

    def _check_dimenstion_update(self, vals):
        return 'finance_dimension_1_id' in vals or 'finance_dimension_2_id' in vals or 'finance_dimension_3_id' in vals
