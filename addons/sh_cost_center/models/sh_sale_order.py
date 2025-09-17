# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ShSaleOrder(models.Model):
    _inherit = 'sale.order'

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


class ShSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sh_cost_center_id = fields.Many2one('sh.cost.center', 'Cost Center')

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(ShSaleOrderLine, self).product_id_change()
        for rec in self:
            rec.sh_cost_center_id = rec.order_id.sh_cost_center_id.id
        return res

    def _prepare_invoice_line(self, **optional_values):
        res = super(
            ShSaleOrderLine, self
        )._prepare_invoice_line(**optional_values)
        res.update({
            'sh_cost_center_id': self.sh_cost_center_id.id,
        })
        return res


class SaleReport(models.Model):
    _inherit = 'sale.report'

    sh_cost_center_id = fields.Many2one(
        'sh.cost.center',
        'Cost Center',
        readonly=True
    )

    def _query(
            self,
            with_clause='',
            fields={},
            groupby='',
            from_clause=''):
        fields['sh_cost_center_id'] = ", l.sh_cost_center_id as sh_cost_center_id"
        from_clause += "left join sh_cost_center c on (c.id=l.sh_cost_center_id)"
        groupby += ', l.sh_cost_center_id'
        return super(
            SaleReport, self
        )._query(with_clause, fields, groupby, from_clause)


class ShSaleMakeInvoice(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        res = super(ShSaleMakeInvoice, self).create_invoices()
        context = self._context
        active_id = context.get('active_id')
        sale_order = self.env['sale.order'].sudo().search([
            ('id', '=', active_id)],
            limit=1
        )
        if res:
            account_invoice = self.env['account.move'].sudo().search([
                ('id', '=', res.get('res_id'))],
                limit=1
            )
            if sale_order and account_invoice:
                account_invoice.sudo().write({
                    'sh_cost_center_id': sale_order.sh_cost_center_id.id,
                })
        return res
