from odoo import fields, models

class AccoountAsset(models.Model):
    _inherit = 'account.asset'
    
    sh_cost_center_id = fields.Many2one('sh.cost.center' ,string='Cost Center')