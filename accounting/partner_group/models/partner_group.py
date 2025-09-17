from odoo import fields, models, api

class PartnerGroup(models.Model):
    _name = 'partner.group'
    _description = "Partner Group"
    _rec_name = 'partner_group'
    
    code = fields.Char(string='Code')
    partner_group = fields.Char(string='Partner Group')
    account_receivable_id = fields.Many2one('account.account', company_dependent=True, domain="[('user_type_id', '=', 'Receivable'), ('company_id', '=', current_company_id)]", required=True)
    account_payable_id = fields.Many2one('account.account', domain="[('user_type_id', '=', 'Payable'),('company_id', '=', current_company_id)]", company_dependent=True, required=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')
    entry_sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    