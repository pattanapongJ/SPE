# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class WizardConfirmWarehouse(models.TransientModel):
    _name = 'wizard.confirm.warehouse'
    _description = "Wizard Confirm Warehouse"

    picking_id = fields.Many2one(comodel_name = "stock.picking", string = "Transfer")
    type_confirm = state = fields.Selection(
        selection=[("warehouse", "Warehouse"), ("warehouse_out", "Warehouse Out")],
        string="Type",
        default="warehouse",
    )
    
    def action_confirm(self):
        self.ensure_one()
        if self.type_confirm == 'warehouse':
            self.picking_id._force_confirm_warehouse()
        elif self.type_confirm == 'warehouse_out':
            self.picking_id._force_confirm_warehouse_out()