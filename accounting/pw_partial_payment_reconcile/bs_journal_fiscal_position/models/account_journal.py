from odoo import api, fields, models

class AcoountJOurnal(models.Model):
    _inherit = 'account.journal'
    
    fiscal_pos_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')