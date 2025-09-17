from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'
    
    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        if 'journal_id' in res:
            res['journal_id']= False
        return res
    
