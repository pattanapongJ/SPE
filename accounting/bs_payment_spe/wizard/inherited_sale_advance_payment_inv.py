from odoo import api, models

class AccountPaymentRegisterInv(models.TransientModel):
    _inherit = 'account.payment.register'
    
    @api.model
    def default_get(self, fields):
        rec = super(AccountPaymentRegisterInv, self).default_get(fields)
        invoice_defaults = self.env['account.move'].browse(self._context.get('active_ids', []))
        if invoice_defaults and len(invoice_defaults) == 1:
            rec['branch_id'] = invoice_defaults.branch_id.id
        else:
            rec['branch_id'] = invoice_defaults[0].branch_id.id
        return rec
    
    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        pass