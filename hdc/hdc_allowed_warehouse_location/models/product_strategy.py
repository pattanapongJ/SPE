# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPutawayRule(models.Model):
    _inherit = 'stock.putaway.rule'

    def _default_location_id(self):
        if self.env.context.get('active_model') == 'stock.location':
            return self.env.context.get('active_id')

    def _get_user_warehouse_domain(self):
        return [('child_ids', '!=', False), '|', ('company_id', '=', False), '&', ('warehouse_id', 'in', self.env.user.allowed_warehouse_ids.ids), ('company_id', '=', self.env.company.id)]
     
    location_in_id = fields.Many2one(
        'stock.location', 'When product arrives in', check_company=True,
        # domain="[('child_ids', '!=', False), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        domain=_get_user_warehouse_domain,
        default=_default_location_id, required=True, ondelete='cascade')
   
    @api.onchange("company_id")
    def _onchange_company(self):
        self.location_in_id = False
        self.location_out_id = False
        if self.company_id:
            
            return {'domain': {'location_in_id':[('child_ids', '!=', False), '|', ('company_id', '=', False), '&', ('warehouse_id', 'in', self.env.user.allowed_warehouse_ids.ids), ('company_id', '=', self.company_id.id)]}}
        else:
            return {'domain': {'location_in_id':[('child_ids', '!=', False), '|', ('company_id', '=', False), '&', ('warehouse_id', 'in', self.env.user.allowed_warehouse_ids.ids), ('company_id', '=', self.env.company.id)]}}
    