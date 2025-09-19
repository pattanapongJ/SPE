# Copyright 2020 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import json

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        string='Allowed Warehouses',
        help='List of all warehouses user has access to',
    )

    allowed_location_ids = fields.Many2many(
        comodel_name='stock.location',
        relation="x_res_users_stock_location_rel",
        column1="res_users_id",
        column2="stock_location_id",
        string='Allowed Locations',
        
    )
       
    @api.model
    def create(self, values):
        user = super(ResUsers, self).create(values)
        check_group_system = user.has_group('base.group_system')
        check_group_erp_manager = user.has_group('base.group_erp_manager')
        if check_group_system or check_group_erp_manager:
            if not user.allowed_warehouse_ids:
                warehouse_ids = self.env["stock.warehouse"].search([])
                if warehouse_ids:
                    user.allowed_warehouse_ids = [(6, 0, warehouse_ids.ids)]

        return user

    def write(self, vals):
        if vals.get('allowed_warehouse_ids') and not vals.get('allowed_location_ids'):
            new_location_ids = []
            for lo in self.allowed_location_ids:
                if ol.warehouse_id.id in vals['allowed_warehouse_ids'][0][2] or lo.warehouse_id.id == False:
                    new_location_ids.append(lo.id)
            vals['allowed_location_ids'] = new_location_ids
                    
        if vals.get('allowed_warehouse_ids'):
            for allowed_warehouse_id in vals['allowed_warehouse_ids'][0][2]:
                warehouse_id = self.env["stock.warehouse"].search([('id', '=', allowed_warehouse_id)], limit= 1)
                if warehouse_id:
                    if warehouse_id[0].user_ids:
                        add_user_id = True
                        for user_id in warehouse_id[0].user_ids:
                            if user_id == self.id:
                                add_user_id = False
                        if add_user_id:
                            warehouse_id[0].write({'user_ids': [(4, self.id)]})

        result = super().write(vals)

        if result and 'allowed_warehouse_ids' in vals:
            self.env['ir.rule'].clear_cache()
        if result and 'allowed_location_ids' in vals:
            self.env['ir.rule'].clear_cache()
        
        return result
