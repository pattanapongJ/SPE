from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def bs_recalculate_tax(self):
        self.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True)