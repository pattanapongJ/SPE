from odoo import api, fields, models


class AccountWithholdingTaxType(models.Model):
    _inherit = "account.withholding.tax"
    
    type = fields.Selection(
        selection=[
            ('sale', 'Sale'),
            ('purchase', 'Purchase'),
            ('none', 'None'), 
        ],
        string='Type',
        store=True,
        default='sale',
        required=True,
    )