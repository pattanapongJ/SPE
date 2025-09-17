from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        line_vals_list = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals)
        if self._context.get('from_payment', False):
            for vals in line_vals_list:
                vals.update(self._get_finance_dimension_values(self._context))
                if write_off_line_vals:
                    for wline in write_off_line_vals:
                        if 'deduct_id' not in wline or vals.get('name') != wline.get('name') or vals.get('account_id') != wline.get(
                                'account_id'):
                            continue
                        deduct_id = wline.get('deduct_id')
                        if deduct_id:
                            vals.update(self._get_finance_dimension_values(wline))
        return line_vals_list

    def _get_finance_dimension_values(self, source):
        return {
            'finance_dimension_1_id': source.get('finance_dimension_1_id'),
            'finance_dimension_2_id': source.get('finance_dimension_2_id'),
            'finance_dimension_3_id': source.get('finance_dimension_3_id')
        }
