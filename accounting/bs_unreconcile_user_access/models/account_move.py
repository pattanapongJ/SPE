from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_reconciled_info_JSON_values(self):
        values = super(AccountMove, self)._get_reconciled_info_JSON_values()
        for val in values:
            val['show_unreconcile_button'] = self.env.user.has_group('bs_unreconcile_user_access.group_unreconcile_user')
        return values
