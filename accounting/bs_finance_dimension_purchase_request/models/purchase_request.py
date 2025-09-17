from odoo import api, fields, models


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _inherit = ['purchase.request', 'bs.base.finance.dimension']

    @api.onchange('finance_dimension_1_id')
    def onchange_finance_dimension_1_id(self):
        self.line_ids.write({
            'finance_dimension_1_id': self.finance_dimension_1_id.id
        })

    @api.onchange('finance_dimension_2_id')
    def onchange_finance_dimension_2_id(self):
        self.line_ids.write({
            'finance_dimension_2_id': self.finance_dimension_2_id.id
        })

    @api.onchange('finance_dimension_3_id')
    def onchange_finance_dimension_3_id(self):
        self.line_ids.write({
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        })


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _inherit = ['purchase.request.line', 'bs.base.finance.dimension']

    @api.model
    def default_get(self, default_fields):
        values = super(PurchaseRequestLine, self).default_get(default_fields)
        if self.request_id:
            self.update({
                'finance_dimension_1_id': self.request_id.finance_dimension_1_id.id,
                'finance_dimension_2_id': self.request_id.finance_dimension_2_id.id,
                'finance_dimension_3_id': self.request_id.finance_dimension_3_id.id
            })

        return values


    # def action_confirm(self):
    #     res = super(StockRequest, self).action_confirm()
    #     for request in self:
    #         request.picking_ids.write(
    #             {
    #                 'finance_dimension_1_id': self.finance_dimension_1_id.id,
    #                 'finance_dimension_2_id': self.finance_dimension_2_id.id,
    #                 'finance_dimension_3_id': self.finance_dimension_3_id.id
    #             }
    #         )
    #         request.move_ids.write(
    #             {
    #                 'finance_dimension_1_id': self.finance_dimension_1_id.id,
    #                 'finance_dimension_2_id': self.finance_dimension_2_id.id,
    #                 'finance_dimension_3_id': self.finance_dimension_3_id.id
    #             }
    #         )
    #     return res
