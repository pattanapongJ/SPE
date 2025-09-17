from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    partial_reconcile_info_ids = fields.One2many(
        'move.partial.reconcile.info',
        compute='_compute_partial_reconcile_info_ids',
        string='Partial Reconciles'
    )

    @api.depends('line_ids.matched_debit_ids', 'line_ids.matched_credit_ids', 'state')
    def _compute_partial_reconcile_info_ids(self):
        for move in self:
            move.partial_reconcile_info_ids = self.env['move.partial.reconcile.info'].search([
                ('move_id', '=', move.id)
            ])

    def _get_reconciled_info_JSON_values(self):
        reconciled_vals = super(AccountMove,self)._get_reconciled_info_JSON_values()
        for val in reconciled_vals:
            if val.get('partial_id'):
                partial = self.env['account.partial.reconcile'].sudo().browse(val.get('partial_id'))
                val['reconcile_date'] = partial.reconcile_date
        return reconciled_vals