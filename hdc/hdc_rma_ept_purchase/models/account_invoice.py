from odoo import fields,models,api

class AccountInvoice(models.Model):
    _inherit = "account.move"

    purchase_claim_id = fields.Many2one('purchase.crm.claim.ept', string='Claim')
    
    @api.model
    def _prepare_refund(self, *args, **kwargs):
        result = super(AccountInvoice, self)._prepare_refund(*args, **kwargs)
        if self.env.context.get('purchase_claim_id'):
            result['purchase_claim_id'] = self.env.context['purchase_claim_id']
        return result