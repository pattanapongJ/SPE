from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'bs.base.finance.dimension']

    @api.onchange('finance_dimension_1_id')
    def onchange_finance_dimension_1_id(self):
        self.order_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_1_id': self.finance_dimension_1_id.id
        })

    @api.onchange('finance_dimension_2_id')
    def onchange_finance_dimension_2_id(self):
        self.order_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_2_id': self.finance_dimension_2_id.id
        })

    @api.onchange('finance_dimension_3_id')
    def onchange_finance_dimension_3_id(self):
        self.order_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        })

    def _prepare_invoice(self):
        _value = super()._prepare_invoice()
        _value.update({
            'finance_dimension_1_id': self.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        })

        return _value

    def _prepare_picking(self):
        _value = super()._prepare_picking()
        _value.update({
            'finance_dimension_1_id': self.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        })

        return _value


class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = ['purchase.order.line', 'bs.base.finance.dimension']

    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        if self.order_id:
            self.update({
            'finance_dimension_1_id': self.order_id.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.order_id.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.order_id.finance_dimension_3_id.id
        })

        return rec


    def _prepare_account_move_line(self, move=False):
        _value = super()._prepare_account_move_line(move)
        _value.update({
            'finance_dimension_1_id': self.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        })
        return _value

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        _value = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty,
                                                                         product_uom)
        _value.update({
            'finance_dimension_1_id': self.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        })
        return _value
