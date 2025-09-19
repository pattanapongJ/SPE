# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.float_utils import float_compare, float_round
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)
    
    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return picking_type[:1]

    user_id = fields.Many2one(
        'res.users', string='Purchase Representative', index=True, tracking=True, readonly=False,
        default=lambda self: self.env.user, check_company=True, states=READONLY_STATES,
        domain=lambda self: [('groups_id', 'in', self.env.ref('purchase.group_purchase_user').id)])

    team_id = fields.Many2one(
        'purchase.team', 'Purchase Team', check_company=True,
        store=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=Purchase.READONLY_STATES, required=True, default=_default_picking_type, domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
        help="This will determine operation type of incoming shipment")
    
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, states=READONLY_STATES, default=lambda self: self.env.company.id)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    # user_id = fields.Many2one(
    #     'res.users', string='Purchase Representative', index=True, tracking=True,
    #     default=lambda self: self.env.user, check_company=True)

    user_id = fields.Many2one('res.users', related='order_id.user_id', string='Purchase Representative', store=True)