from odoo import api, fields, models, _


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    partial_exchange_move_id = fields.Many2one(comodel_name='account.move')

    def unlink(self):
        if not self:
            return True
        self = self.with_context(partial_exchange_move_id=self.partial_exchange_move_id.ids)
        return super(AccountPartialReconcile,self).unlink()

        # # Retrieve the matching number to unlink.
        # full_to_unlink = self.full_reconcile_id

        # # Retrieve the CABA entries to reverse.
        # moves_to_reverse = self.env['account.move'].search([('tax_cash_basis_rec_id', 'in', self.ids)])

        # moves_to_reverse += self.partial_exchange_move_id

        # # Unlink partials before doing anything else to avoid 'Record has already been deleted' due to the recursion.
        # res = super().unlink()

        # # Reverse CABA entries.
        # default_values_list = [{
        #     'date': move._get_accounting_date(move.date, move._affect_tax_report()),
        #     'ref': _('Reversal of: %s') % move.name,
        # } for move in moves_to_reverse]
        # moves_to_reverse._reverse_moves(default_values_list, cancel=True)

        # if full_to_unlink.exists():
        #     # Remove the matching numbers.
        #     full_to_unlink.unlink()

        # return res
