# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ShPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def default_cost_center(self):
        if self.env.user.sh_cost_center_id:
            return self.env.user.sh_cost_center_id.id
        return False

    sh_cost_center_id = fields.Many2one(
        'sh.cost.center',
        'Cost Center',
        default=default_cost_center
    )

    @api.onchange('sh_cost_center_id')
    def onchange_sh_cost_center_id(self):
        for rec in self:
            if rec.sh_cost_center_id:
                for line in rec.order_line:
                    line.sh_cost_center_id = rec.sh_cost_center_id.id

    def _prepare_invoice(self):
        res = super(ShPurchaseOrder, self)._prepare_invoice()
        res.update({
            'sh_cost_center_id': self.sh_cost_center_id.id,
        })
        return res


class ShPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sh_cost_center_id = fields.Many2one('sh.cost.center', 'Cost Center')

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(ShPurchaseOrderLine, self).onchange_product_id()
        for rec in self:
            rec.sh_cost_center_id = rec.order_id.sh_cost_center_id.id
        return res

    def _prepare_account_move_line(self, move=False):
        res = super(
            ShPurchaseOrderLine, self
        )._prepare_account_move_line(move=move)
        res.update({
            'sh_cost_center_id': self.sh_cost_center_id.id,
        })
        return res


class ShPurchaseReport(models.Model):
    _inherit = "purchase.report"

    sh_cost_center_id = fields.Many2one(
        'sh.cost.center',
        'Cost Center',
        readonly=True
    )

    def _select(self):
        return super(ShPurchaseReport, self)._select() + ", l.sh_cost_center_id as sh_cost_center_id"

    def _from(self):
        return super(ShPurchaseReport, self)._from() + " left join sh_cost_center center on(l.sh_cost_center_id=center.id)"

    def _group_by(self):
        return super(ShPurchaseReport, self)._group_by() + ", l.sh_cost_center_id"
