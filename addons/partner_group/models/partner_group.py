from odoo import fields, models

class PartnerGroup(models.Model):
    _name = 'partner.group'
    _description = "Partner Group"
    _rec_name = 'partner_group'
    
    code = fields.Char(string='Code')
    partner_group = fields.Char(string='Partner Group')
    account_receivable_id = fields.Many2one('account.account', domain=[('user_type_id', '=', 'Receivable')], required=True)
    account_payable_id = fields.Many2one('account.account', domain=[('user_type_id', '=', 'Payable')], required=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')
    