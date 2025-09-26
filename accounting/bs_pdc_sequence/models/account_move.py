from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_pdc_entry = fields.Boolean(string='Is PDC Entry?',default=False,copy=True)




class PDCWizard(models.Model):
    _inherit = 'pdc.wizard'

    def get_move_vals_effective_date(self, debit_line, credit_line):
        move_vals = super().get_move_vals_effective_date(debit_line, credit_line)
        move_vals['is_pdc_entry'] = True
        return move_vals
