# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _default_warehouse_id(self):
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id),('is_default_warehouse', '=', True)], limit=1)
        return warehouse_id
    
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_default_warehouse_id, check_company=True)
    
    @api.onchange('company_id')
    def _onchange_company_id(self):
        super()._onchange_company_id()
        if self.company_id:
            warehouse_id = self._default_warehouse_id()
            warehouse_id = warehouse_id.id
            self.warehouse_id = warehouse_id

    @api.onchange('user_id')
    def onchange_user_id(self):
        super().onchange_user_id()
        if self.state in ['draft','sent']:
            warehouse_id = self._default_warehouse_id()
            warehouse_id = warehouse_id.id
            self.warehouse_id = warehouse_id

    