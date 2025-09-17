from odoo import api, models

class DecimalPrecisions(models.Model):
    _inherit = 'decimal.precision'
    
    @api.model
    def init(self):
        precision_data = [
            {'name': 'Conversion Factor', 'digits': 6},
            {'name': 'Custom Unit Price 1', 'digits': 6},
            {'name': 'Custom Unit Price 2', 'digits': 6},
        ]

        for precision in precision_data:
            existing_precision = self.env['decimal.precision'].search([('name', '=', precision['name'])], limit=1)
            if existing_precision:
                existing_precision.write({'digits': precision['digits']})
            else:
                self.env['decimal.precision'].create(precision)