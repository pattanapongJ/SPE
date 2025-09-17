from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('user_id')
    def onchange_user_id(self):
        super(SaleOrder, self).onchange_user_id()
        _dimension_datas = self.env.ref('bs_finance_dimension.bs_dimension_2').finance_dimension_ids.filtered(
            lambda x: x.res_id == self.user_id.id)
        if _dimension_datas:
            self.finance_dimension_2_id = _dimension_datas[0]
        else:
            self.finance_dimension_2_id = None

    @api.onchange('finance_dimension_4_id')
    def onchange_finance_dimension_4_id(self):
        self.order_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_4_id': self.finance_dimension_4_id.id
        })

    @api.onchange('finance_dimension_5_id')
    def onchange_finance_dimension_5_id(self):
        self.order_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_5_id': self.finance_dimension_5_id.id
        })

    @api.onchange('finance_dimension_6_id')
    def onchange_finance_dimension_6_id(self):
        self.order_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_6_id': self.finance_dimension_6_id.id
        })

    @api.onchange('finance_dimension_7_id')
    def onchange_finance_dimension_7_id(self):
        self.order_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_7_id': self.finance_dimension_7_id.id
        })

    @api.onchange('finance_dimension_8_id')
    def onchange_finance_dimension_8_id(self):
        self.order_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_8_id': self.finance_dimension_8_id.id
        })

    @api.onchange('finance_dimension_9_id')
    def onchange_finance_dimension_9_id(self):
        self.order_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_9_id': self.finance_dimension_9_id.id
        })

    @api.onchange('finance_dimension_10_id')
    def onchange_finance_dimension_10_id(self):
        self.order_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_10_id': self.finance_dimension_10_id.id
        })

    def _prepare_invoice(self):
        _value = super()._prepare_invoice()
        _value.update({
            'finance_dimension_4_id': self.finance_dimension_4_id.id,
            'finance_dimension_5_id': self.finance_dimension_5_id.id,
            'finance_dimension_6_id': self.finance_dimension_6_id.id,
            'finance_dimension_7_id': self.finance_dimension_7_id.id,
            'finance_dimension_8_id': self.finance_dimension_8_id.id,
            'finance_dimension_9_id': self.finance_dimension_9_id.id,
            'finance_dimension_10_id': self.finance_dimension_10_id.id
        })
        return _value

    def _check_required_dimensions(self):
        for rec in self.filtered(lambda x: x.state in ['draft', 'sent']):
            for line in rec.order_line.filtered(lambda x: not x.display_type):
                _dimension1 = self.env.ref('bs_finance_dimension.bs_dimension_1', raise_if_not_found=False)
                _dimension2 = self.env.ref('bs_finance_dimension.bs_dimension_2', raise_if_not_found=False)
                _dimension3 = self.env.ref('bs_finance_dimension.bs_dimension_3', raise_if_not_found=False)
                _dimension4 = self.env.ref('bs_finance_dimension_spe.bs_dimension_4', raise_if_not_found=False)
                _dimension5 = self.env.ref('bs_finance_dimension_spe.bs_dimension_5', raise_if_not_found=False)
                _dimension6 = self.env.ref('bs_finance_dimension_spe.bs_dimension_6', raise_if_not_found=False)
                _dimension7 = self.env.ref('bs_finance_dimension_spe.bs_dimension_7', raise_if_not_found=False)
                _dimension8 = self.env.ref('bs_finance_dimension_spe.bs_dimension_8', raise_if_not_found=False)
                _dimension9 = self.env.ref('bs_finance_dimension_spe.bs_dimension_9', raise_if_not_found=False)
                _dimension10 = self.env.ref('bs_finance_dimension_spe.bs_dimension_10', raise_if_not_found=False)

                if line.need_finance_dimension_1:
                    raise ValidationError(_('%s is required.', _dimension1.name if _dimension1 else 'Dimension 1'))
                if line.need_finance_dimension_2:
                    raise ValidationError(_('%s is required.', _dimension2.name if _dimension2 else 'Dimension 2'))
                if line.need_finance_dimension_3:
                    raise ValidationError(_('%s is required.', _dimension3.name if _dimension3 else 'Dimension 3'))
                if line.need_finance_dimension_4:
                    raise ValidationError(_('%s is required.', _dimension4.name if _dimension4 else 'Dimension 4'))
                if line.need_finance_dimension_5:
                    raise ValidationError(_('%s is required.', _dimension5.name if _dimension5 else 'Dimension 5'))
                if line.need_finance_dimension_6:
                    raise ValidationError(_('%s is required.', _dimension6.name if _dimension6 else 'Dimension 6'))
                if line.need_finance_dimension_7:
                    raise ValidationError(_('%s is required.', _dimension7.name if _dimension7 else 'Dimension 7'))
                if line.need_finance_dimension_8:
                    raise ValidationError(_('%s is required.', _dimension8.name if _dimension8 else 'Dimension 8'))
                if line.need_finance_dimension_9:
                    raise ValidationError(_('%s is required.', _dimension9.name if _dimension9 else 'Dimension 9'))
                if line.need_finance_dimension_10:
                    raise ValidationError(_('%s is required.', _dimension10.name if _dimension10 else 'Dimension 10'))

    def action_confirm(self):
        self._check_required_dimensions()
        res = super(SaleOrder, self).action_confirm()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    need_finance_dimension_1 = fields.Boolean(string=_('Need Dimension 1'), compute='_compute_required_dimension',
                                              default=False)
    need_finance_dimension_2 = fields.Boolean(string=_('Need Dimension 2'), compute='_compute_required_dimension',
                                              default=False)
    need_finance_dimension_3 = fields.Boolean(string=_('Need Dimension 3'), compute='_compute_required_dimension',
                                              default=False)
    need_finance_dimension_4 = fields.Boolean(string=_('Need Dimension 4'), compute='_compute_required_dimension',
                                              default=False)
    need_finance_dimension_5 = fields.Boolean(string=_('Need Dimension 5'), compute='_compute_required_dimension',
                                              default=False)
    need_finance_dimension_6 = fields.Boolean(string=_('Need Dimension 6'), compute='_compute_required_dimension',
                                              default=False)
    need_finance_dimension_7 = fields.Boolean(string=_('Need Dimension 7'), compute='_compute_required_dimension',
                                              default=False)
    need_finance_dimension_8 = fields.Boolean(string=_('Need Dimension 8'), compute='_compute_required_dimension',
                                              default=False)
    need_finance_dimension_9 = fields.Boolean(string=_('Need Dimension 9'), compute='_compute_required_dimension',
                                              default=False)
    need_finance_dimension_10 = fields.Boolean(string=_('Need Dimension 10'), compute='_compute_required_dimension',
                                               default=False)

    @api.depends('state', 'product_template_id', 'order_id.fiscal_position_id')
    def _compute_required_dimension(self):
        for rec in self:
            fiscal_position = rec.order_id.fiscal_position_id
            accounts = rec.product_template_id.get_product_accounts(fiscal_pos=fiscal_position)
            account_id = accounts['income']

            rec.need_finance_dimension_1 = account_id.need_finance_dimension_1 and rec.state == 'draft' and not rec.finance_dimension_1_id
            rec.need_finance_dimension_2 = account_id.need_finance_dimension_2 and rec.state == 'draft' and not rec.finance_dimension_2_id
            rec.need_finance_dimension_3 = account_id.need_finance_dimension_3 and rec.state == 'draft' and not rec.finance_dimension_3_id
            rec.need_finance_dimension_4 = account_id.need_finance_dimension_4 and rec.state == 'draft' and not rec.finance_dimension_4_id
            rec.need_finance_dimension_5 = account_id.need_finance_dimension_5 and rec.state == 'draft' and not rec.finance_dimension_5_id
            rec.need_finance_dimension_6 = account_id.need_finance_dimension_6 and rec.state == 'draft' and not rec.finance_dimension_6_id
            rec.need_finance_dimension_7 = account_id.need_finance_dimension_7 and rec.state == 'draft' and not rec.finance_dimension_7_id
            rec.need_finance_dimension_8 = account_id.need_finance_dimension_8 and rec.state == 'draft' and not rec.finance_dimension_8_id
            rec.need_finance_dimension_9 = account_id.need_finance_dimension_9 and rec.state == 'draft' and not rec.finance_dimension_9_id
            rec.need_finance_dimension_10 = account_id.need_finance_dimension_10 and rec.state == 'draft' and not rec.finance_dimension_10_id

    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        if self.order_id:
            self.update({
                'finance_dimension_4_id': self.finance_dimension_4_id or self.order_id.finance_dimension_4_id.id,
                'finance_dimension_5_id': self.finance_dimension_5_id or self.order_id.finance_dimension_5_id.id,
                'finance_dimension_6_id': self.finance_dimension_6_id or self.order_id.finance_dimension_6_id.id,
                'finance_dimension_7_id': self.finance_dimension_7_id or self.order_id.finance_dimension_7_id.id,
                'finance_dimension_8_id': self.finance_dimension_8_id or self.order_id.finance_dimension_8_id.id,
                'finance_dimension_9_id': self.finance_dimension_9_id or self.order_id.finance_dimension_9_id.id,
                'finance_dimension_10_id': self.finance_dimension_10_id or self.order_id.finance_dimension_10_id.id
            })

        return rec

    def _prepare_invoice_line(self, **optional_values):
        _value = super()._prepare_invoice_line(**optional_values)
        _value.update({
            'finance_dimension_4_id': self.finance_dimension_4_id.id,
            'finance_dimension_5_id': self.finance_dimension_5_id.id,
            'finance_dimension_6_id': self.finance_dimension_6_id.id,
            'finance_dimension_7_id': self.finance_dimension_7_id.id,
            'finance_dimension_8_id': self.finance_dimension_8_id.id,
            'finance_dimension_9_id': self.finance_dimension_9_id.id,
            'finance_dimension_10_id': self.finance_dimension_10_id.id
        })
        return _value

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        res = super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)
        orders = list(set(x.order_id for x in self))
        for order in orders:
            picking_ids = order.picking_ids.filtered(lambda x: x.state not in ['cancel', 'done'])
            if picking_ids:
                picking_ids.write({
                    'finance_dimension_4_id': order.finance_dimension_4_id.id,
                    'finance_dimension_5_id': order.finance_dimension_5_id.id,
                    'finance_dimension_6_id': order.finance_dimension_6_id.id,
                    'finance_dimension_7_id': order.finance_dimension_7_id.id,
                    'finance_dimension_8_id': order.finance_dimension_8_id.id,
                    'finance_dimension_9_id': order.finance_dimension_9_id.id,
                    'finance_dimension_10_id': order.finance_dimension_10_id.id
                })

        for line in self:
            for move in line.move_ids.filtered(lambda x: x.state not in ['cancel', 'done']):
                move.write({
                    'finance_dimension_4_id': line.finance_dimension_4_id.id,
                    'finance_dimension_5_id': line.finance_dimension_5_id.id,
                    'finance_dimension_6_id': line.finance_dimension_6_id.id,
                    'finance_dimension_7_id': line.finance_dimension_7_id.id,
                    'finance_dimension_8_id': line.finance_dimension_8_id.id,
                    'finance_dimension_9_id': line.finance_dimension_9_id.id,
                    'finance_dimension_10_id': line.finance_dimension_10_id.id
                })

        return res
