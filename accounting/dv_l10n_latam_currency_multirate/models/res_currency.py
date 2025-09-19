from odoo import api, fields, models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    _sql_constraints = [
        ('unique_name', 'CHECK(1=1)','Error Message'),
        ('unique_type_name', 'unique (name,rate_type)',
         'The currency code already exists in this rate type!'),
        ('rounding_gt_zero', 'CHECK (rounding>0)',
         'The rounding factor must be greater than 0!')
    ]
    
    rate_type = fields.Selection([
        ('buy', 'Buying'),
        ('sell', 'Selling'),
        ('average', 'Average'),
        ('close', 'Closing'),
    ], string='Currency Type', default='buy')
    def name_get(self):
        res = []
        for currency in self:
            if currency.rate_type:
                if currency.rate_type == 'buy':
                    rate_type = 'Buying'
                elif currency.rate_type == 'sell':
                    rate_type = 'Selling'
                elif currency.rate_type == 'average':
                        rate_type = 'Average'
                elif currency.rate_type == 'close':
                    rate_type = 'Closing'                    
                complete_name = '%s / %s ' % (currency.name, rate_type)
            else:
                complete_name = currency.name
            res.append((currency.id, complete_name))
        return res
