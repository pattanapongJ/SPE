# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero
from odoo.tools.misc import OrderedSet


class StockInventoryAllowed(models.Model):
    _inherit = "stock.inventory"

    def _get_user_warehouse_domain(self):
        return [('warehouse_id', 'in', self.env.user.allowed_warehouse_ids.ids), ('company_id', '=', self.env.company.id), ('usage', 'in', ['internal', 'transit'])]
        
    location_ids = fields.Many2many(
        'stock.location', string='Locations',
        readonly=True, check_company=True,
        states={'draft': [('readonly', False)]},
        domain=_get_user_warehouse_domain)
    
    @api.onchange("company_id")
    def _onchange_company(self):
        if self.company_id:
            return {'domain': {'location_ids':[('warehouse_id', 'in', self.env.user.allowed_warehouse_ids.ids), ('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])]}}
        else:
            return {'domain': {'location_ids':[('warehouse_id', 'in', self.env.user.allowed_warehouse_ids.ids), ('company_id', '=', self.env.company.id), ('usage', 'in', ['internal', 'transit'])]}}
    