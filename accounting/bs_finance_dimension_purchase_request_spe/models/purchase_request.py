from odoo import api, fields, models

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    @api.onchange('finance_dimension_4_id')
    def onchange_finance_dimension_4_id(self):
        self.line_ids.write({
            'finance_dimension_4_id': self.finance_dimension_4_id.id
        })

    @api.onchange('finance_dimension_5_id')
    def onchange_finance_dimension_5_id(self):
        self.line_ids.write({
            'finance_dimension_5_id': self.finance_dimension_5_id.id
        })

    @api.onchange('finance_dimension_6_id')
    def onchange_finance_dimension_6_id(self):
        self.line_ids.write({
            'finance_dimension_6_id': self.finance_dimension_6_id.id
        })
        
    @api.onchange('finance_dimension_7_id')
    def onchange_finance_dimension_7_id(self):
        self.line_ids.write({
            'finance_dimension_7_id': self.finance_dimension_7_id.id
        })
    
    
    @api.onchange('finance_dimension_8_id')
    def onchange_finance_dimension_8_id(self):
        self.line_ids.write({
            'finance_dimension_8_id': self.finance_dimension_8_id.id
        })
    
    @api.onchange('finance_dimension_9_id')
    def onchange_finance_dimension_9_id(self):
        self.line_ids.write({
            'finance_dimension_9_id': self.finance_dimension_9_id.id
        })
    
    
    @api.onchange('finance_dimension_10_id')
    def onchange_finance_dimension_10_id(self):
        self.line_ids.write({
            'finance_dimension_10_id': self.finance_dimension_10_id.id
        })


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    @api.model
    def default_get(self, default_fields):
        values = super(PurchaseRequestLine, self).default_get(default_fields)
        if self.request_id:
            self.update({
                'finance_dimension_4_id': self.request_id.finance_dimension_4_id.id,
                'finance_dimension_5_id': self.request_id.finance_dimension_5_id.id,
                'finance_dimension_6_id': self.request_id.finance_dimension_6_id.id,
                'finance_dimension_7_id': self.request_id.finance_dimension_7_id.id,
                'finance_dimension_8_id': self.request_id.finance_dimension_8_id.id,
                'finance_dimension_9_id': self.request_id.finance_dimension_9_id.id,
                'finance_dimension_10_id': self.request_id.finance_dimension_10_id.id
            })

        return values


