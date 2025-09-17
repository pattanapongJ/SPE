from odoo import api, fields, models


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'bs.base.finance.dimension']

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


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'bs.base.finance.dimension']

    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        if self.order_id:
            self.update({
                'finance_dimension_1_id': self.finance_dimension_1_id or self.order_id.finance_dimension_1_id.id,
                'finance_dimension_2_id': self.finance_dimension_2_id or self.order_id.finance_dimension_2_id.id,
                'finance_dimension_3_id': self.finance_dimension_3_id or self.order_id.finance_dimension_3_id.id
            })

        return rec

    def _prepare_invoice_line(self, **optional_values):
        _value = super()._prepare_invoice_line(**optional_values)
        _value.update({
            'finance_dimension_1_id': self.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        })
        return _value

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        res = super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)
        orders = list(set(x.order_id for x in self))
        for order in orders:
            picking_ids = order.picking_ids.filtered(lambda x:x.state not in ['cancel','done'])
            if picking_ids:
                picking_ids.write({
                    'finance_dimension_1_id': order.finance_dimension_1_id.id,
                    'finance_dimension_2_id': order.finance_dimension_2_id.id,
                    'finance_dimension_3_id': order.finance_dimension_3_id.id
                })

        for line in self:
            for move in line.move_ids.filtered(lambda x:x.state not in ['cancel','done']):
                move.write({
                    'finance_dimension_1_id': line.finance_dimension_1_id.id,
                    'finance_dimension_2_id': line.finance_dimension_2_id.id,
                    'finance_dimension_3_id': line.finance_dimension_3_id.id
                })

        return res
