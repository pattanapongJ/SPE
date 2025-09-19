from odoo import _, api, fields, models


class AccountPaymentDeduction(models.TransientModel):
    _inherit = 'account.payment.deduction'
    
    sh_cost_center_id = fields.Many2one('sh.cost.center', string='Cost Center')
    analytic_account_id = fields.Many2one('account.analytic.account')