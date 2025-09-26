from odoo import api, fields, models


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = 'purchase.request.line.make.purchase.order'

    @api.model
    def _prepare_purchase_order_line(self, po, item):
        _value = super(PurchaseRequestLineMakePurchaseOrder, self)._prepare_purchase_order_line(po, item)
        _value.update({
            'finance_dimension_1_id': item.line_id.finance_dimension_1_id.id,
            'finance_dimension_2_id': item.line_id.finance_dimension_2_id.id,
            'finance_dimension_3_id': item.line_id.finance_dimension_3_id.id
        })

        purchase = self.env['purchase.order'].sudo().browse(_value.get('order_id'))
        if purchase.exists():
            purchase.sudo().write({
                'finance_dimension_1_id': item.request_id.finance_dimension_1_id.id,
                'finance_dimension_2_id': item.request_id.finance_dimension_2_id.id,
                'finance_dimension_3_id': item.request_id.finance_dimension_3_id.id
            })
        return _value