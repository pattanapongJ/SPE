# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

class Quotations(models.Model):
    _inherit = 'quotation.order'

    @api.model
    def _default_warehouse_id(self):
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id),('is_default_warehouse', '=', True)], limit=1)
        return warehouse_id
    
    warehouse_id = fields.Many2one('stock.warehouse', string = 'Warehouse', required = True, readonly = True,
        states = {'draft': [('readonly', False)], 'sent': [('readonly', False)]}, default = _default_warehouse_id,
        check_company = True)