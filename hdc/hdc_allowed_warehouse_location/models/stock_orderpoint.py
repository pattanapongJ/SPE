# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, _, api, fields, models, registry
from odoo.exceptions import UserError, ValidationError


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    def _get_location_domain(self):
        return ['|', ('warehouse_id', '=', False), ('warehouse_id', 'in', self.env.user.allowed_warehouse_ids.ids)]
    
    def _get_warehouse_domain(self):
        return [('user_ids', 'in', self.env.user.id)]
    
    @api.model
    def _default_location_id(self):
        return self.env['stock.location'].search([('warehouse_id', '=', 3)], limit=1)

    location_id = fields.Many2one(
        'stock.location', 'Location', index=True,
        ondelete="cascade", required=True, check_company=True, domain=_get_location_domain, default=lambda self: self._default_location_id())
    
    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Warehouse',
        check_company=True, ondelete="cascade", required=True, domain=_get_warehouse_domain)
    
    
    @api.onchange('location_id')
    def _onchange_location_id(self):
        warehouse = self.location_id.get_warehouse().id
        if warehouse:
            self.warehouse_id = warehouse

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """ Finds location id for changed warehouse. """
        if self.warehouse_id:
            self.location_id = self.warehouse_id.lot_stock_id.id
        else:
            self.location_id = False
            
    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.warehouse_id = self.env['stock.warehouse'].search([
                ('company_id', '=', self.company_id.id), ('user_ids', 'in', self.env.user.id)
            ], limit=1)
            
        