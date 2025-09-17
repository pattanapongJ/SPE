from odoo import api, fields, models


class StockRequestOrder(models.Model):
    _name = 'stock.request.order'
    _inherit = ['stock.request.order', 'bs.base.finance.dimension']

    @api.onchange('finance_dimension_1_id')
    def onchange_finance_dimension_1_id(self):
        self.stock_request_ids.write({
            'finance_dimension_1_id': self.finance_dimension_1_id.id
        })

    @api.onchange('finance_dimension_2_id')
    def onchange_finance_dimension_2_id(self):
        self.stock_request_ids.write({
            'finance_dimension_2_id': self.finance_dimension_2_id.id
        })

    @api.onchange('finance_dimension_3_id')
    def onchange_finance_dimension_3_id(self):
        self.stock_request_ids.write({
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        })


class StockRequest(models.Model):
    _name = 'stock.request'
    _inherit = ['stock.request', 'bs.base.finance.dimension']

    @api.model
    def default_get(self, default_fields):
        values = super(StockRequest, self).default_get(default_fields)
        if self.order_id:
            self.update({
                'finance_dimension_1_id':self.finance_dimension_1_id or self.order_id.finance_dimension_1_id,
                'finance_dimension_2_id':self.finance_dimension_2_id or self.order_id.finance_dimension_2_id,
                'finance_dimension_3_id':self.finance_dimension_3_id or self.order_id.finance_dimension_3_id
            })

        return values


    def action_confirm(self):
        res = super(StockRequest, self).action_confirm()
        for request in self:
            # request.picking_ids.write(
            #     {
            #         'finance_dimension_1_id': self.finance_dimension_1_id.id,
            #         'finance_dimension_2_id': self.finance_dimension_2_id.id,
            #         'finance_dimension_3_id': self.finance_dimension_3_id.id
            #     }
            # )
            request.move_ids.write(
                {
                    'finance_dimension_1_id': request.finance_dimension_1_id.id,
                    'finance_dimension_2_id': request.finance_dimension_2_id.id,
                    'finance_dimension_3_id': request.finance_dimension_3_id.id
                }
            )
            # request.purchase_ids.write(
            #     {
            #         'finance_dimension_1_id': self.finance_dimension_1_id.id,
            #         'finance_dimension_2_id': self.finance_dimension_2_id.id,
            #         'finance_dimension_3_id': self.finance_dimension_3_id.id
            #     }
            # )
            request.purchase_line_ids.write(
                {
                    'finance_dimension_1_id': request.finance_dimension_1_id.id,
                    'finance_dimension_2_id': request.finance_dimension_2_id.id,
                    'finance_dimension_3_id': request.finance_dimension_3_id.id
                }
            )
        return res
