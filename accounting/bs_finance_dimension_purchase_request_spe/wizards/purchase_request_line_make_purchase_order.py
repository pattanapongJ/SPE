from odoo import api, fields, models


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = 'purchase.request.line.make.purchase.order'

    @api.model
    def _prepare_purchase_order_line(self, po, item):
        _value = super(PurchaseRequestLineMakePurchaseOrder, self)._prepare_purchase_order_line(po, item)
        _value.update({
            'finance_dimension_4_id': item.line_id.finance_dimension_4_id.id,
            'finance_dimension_5_id': item.line_id.finance_dimension_5_id.id,
            'finance_dimension_6_id': item.line_id.finance_dimension_6_id.id,
            'finance_dimension_7_id': item.line_id.finance_dimension_7_id.id,
            'finance_dimension_8_id': item.line_id.finance_dimension_8_id.id,
            'finance_dimension_9_id': item.line_id.finance_dimension_9_id.id,
            'finance_dimension_10_id': item.line_id.finance_dimension_10_id.id
        })

        purchase = self.env['purchase.order'].sudo().browse(_value.get('order_id'))
        if purchase.exists():
            purchase.sudo().write({
                'finance_dimension_4_id': item.request_id.finance_dimension_4_id.id,
                'finance_dimension_5_id': item.request_id.finance_dimension_5_id.id,
                'finance_dimension_6_id': item.request_id.finance_dimension_6_id.id,
                'finance_dimension_7_id': item.request_id.finance_dimension_7_id.id,
                'finance_dimension_8_id': item.request_id.finance_dimension_8_id.id,
                'finance_dimension_9_id': item.request_id.finance_dimension_9_id.id,
                'finance_dimension_10_id': item.request_id.finance_dimension_10_id.id
            })
        return _value
