from odoo import _, api, fields, models


class AccountPaymentDeduction(models.TransientModel):
    _inherit = 'account.payment.deduction'
    
    multi_deduct_group_line_id = fields.Many2one('payment.multi.deduct.line',string='Name')

    @api.onchange('multi_deduct_group_line_id')
    def onchange_multi_deduct_group_line_id(self):
        self.account_id = self.multi_deduct_group_line_id.account_id
