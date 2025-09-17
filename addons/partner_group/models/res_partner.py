from odoo import models,fields,api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    partner_group_id = fields.Many2one('partner.group', string='Partner Group', required=True)
    
    @api.onchange('partner_group_id')
    def _oncahnge_patner_group(self):
        for account in self:
            account.property_account_receivable_id = account.partner_group_id.account_receivable_id
            account.property_account_payable_id = account.partner_group_id.account_payable_id
            account.property_account_position_id = account.partner_group_id.fiscal_position_id