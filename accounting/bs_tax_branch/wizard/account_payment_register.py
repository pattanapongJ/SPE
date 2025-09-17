from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountPaymentRegisters(models.TransientModel):
    _inherit = 'account.payment.register'
    
    branch_id = fields.Many2one('res.branch', required=True, store=True, readonly=False, compute='_compute_branch')
    
    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        move = self.env['account.move'].browse(self.env.context.get('active_id'))
        selected_branch = self.branch_id
        if move:
            if selected_branch:
                if self.branch_id.id != move.branch_id.id:
                    raise UserError("Please select active branch only. Other may create the Multi branch issue. \n\ne.g: If you wish to add other branch then Switch branch from the header and set that.")
        else:
            selected_branch = self.branch_id
        
    
    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        # update branch id on payment
        payment_vals.update({
            'branch_id': self.branch_id.id
        })
        return payment_vals
    
    def _create_payment_vals_from_batch(self, batch_result):
        res = super()._create_payment_vals_from_batch(batch_result)
        move = self.env['account.move'].browse(self.env.context.get('active_ids'))[0]
        if move.branch_id:
            self.branch_id = move.branch_id.id
        res.update({
            'branch_id': self.branch_id.id
        })
        
        return res
    
    @api.depends('can_edit_wizard')
    def _compute_branch(self):
        for wizard in self:
            if wizard.can_edit_wizard:
                batches = wizard._get_batches()
                batch = batches[0]['lines'][0]
                wizard.branch_id = batch.branch_id.id
            else:
                wizard.branch_id = False
