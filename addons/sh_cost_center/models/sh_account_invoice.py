# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ShAccountInvoice(models.Model):
    _inherit = 'account.move'

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
    def _onchange_partner_id(self):
        for rec in self:
            if rec.sh_cost_center_id:
                for line in rec.invoice_line_ids:
                    line.sh_cost_center_id = rec.sh_cost_center_id.id


class ShAccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    sh_cost_center_id = fields.Many2one('sh.cost.center', 'Cost Center')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(ShAccountInvoiceLine, self)._onchange_product_id()
        if self:
            for rec in self:
                rec.sh_cost_center_id = rec.move_id.sh_cost_center_id.id
        return res


class ShAccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    sh_cost_center_id = fields.Many2one(
        'sh.cost.center',
        'Cost Center',
        readonly=True
    )

    def _select(self):
        return super(ShAccountInvoiceReport, self)._select() + ",line.sh_cost_center_id"

    @api.model
    def _from(self):
        return super(ShAccountInvoiceReport, self)._from() + "LEFT JOIN sh_cost_center center ON center.id=line.sh_cost_center_id"

    def _group_by(self):
        return super(ShAccountInvoiceReport, self)._group_by() + ",line.sh_cost_center_id"
