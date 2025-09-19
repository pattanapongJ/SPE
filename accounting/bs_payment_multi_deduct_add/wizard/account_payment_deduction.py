from odoo import _, api, fields, models


class AccountPaymentDeduction(models.TransientModel):
    _inherit = "account.payment.deduction"

    gl_item_id = fields.Many2one('account.move.line',string='GL item',)