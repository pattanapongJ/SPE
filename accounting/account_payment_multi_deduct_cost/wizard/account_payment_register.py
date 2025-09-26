# from paramiko.agent import value

from odoo import models

class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"
    
    def _prepare_deduct_move_line(self, deduct):
        val = super(AccountPaymentRegister,self)._prepare_deduct_move_line(deduct)
        val.update({
            "analytic_account_id": deduct.analytic_account_id.id,
            "sh_cost_center_id": deduct.sh_cost_center_id.id
        })
        return val