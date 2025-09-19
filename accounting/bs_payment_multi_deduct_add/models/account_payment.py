from odoo import models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        self.line_ids.action_reconcile_with_offset_move_line()
        return res

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        line_vals_list = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals)
        if write_off_line_vals:
            for vals in line_vals_list:
                if isinstance(write_off_line_vals, list):
                    for wline in write_off_line_vals:
                        if 'deduct_id' not in wline or vals.get('name') != wline.get('name') or vals.get(
                                'account_id') != wline.get(
                            'account_id'):
                            continue
                        deduct_id = wline.get('deduct_id')
                        if deduct_id:
                            vals.update(self._extra_deduct_line_val(wline))
                else:
                    if 'deduct_id' not in write_off_line_vals or vals.get('name') != write_off_line_vals.get(
                            'name') or vals.get('account_id') != write_off_line_vals.get('account_id'):
                        continue
                    deduct_id = write_off_line_vals.get('deduct_id')
                    if deduct_id:
                        vals.update(self._extra_deduct_line_val(write_off_line_vals))

        return line_vals_list

    def _extra_deduct_line_val(self, wline):
        return {
            'offset_move_line_id': wline.get('offset_move_line_id')
        }

    def _synchronize_from_moves(self, changed_fields):
        if self.line_ids.mapped('offset_move_line_id'):
            self = self.with_context(skip_account_move_synchronization=True)
        super(AccountPayment, self)._synchronize_from_moves(changed_fields)
