from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    @api.onchange('move_ids')
    def onchange_move_ids(self):
        domain=[('show_in_credit_note','=',True)]
        if self.move_type in ['out_invoice','out_refund']:
            domain.append(('type','=','sale'),)
        elif self.move_type in ['in_invoice','in_refund']:
            domain.append(('type', '=', 'purchase'))
        return {'domain': {'journal_id': domain}}