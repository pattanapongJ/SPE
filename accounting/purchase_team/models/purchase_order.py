# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    user_id = fields.Many2one(
        'res.users', string='Purchase Representative', index=True, tracking=True, readonly=False,
        default=lambda self: self.env.user, check_company=True, states=READONLY_STATES,
        domain=lambda self: [('groups_id', 'in', self.env.ref('purchase.group_purchase_user').id)])

    team_id = fields.Many2one(
        'purchase.team', 'Purchase Team', check_company=True,
        store=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.onchange('user_id')
    def onchange_user_id(self):
        if self.user_id:
            self.team_id = self.env['purchase.team']._get_default_purchase_team_id(user_id=self.user_id.id)

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res['purchase_team_id'] = self.team_id and self.team_id.id or False
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    user_id = fields.Many2one('res.users', related='order_id.user_id', string='Purchase Representative', store=True)
