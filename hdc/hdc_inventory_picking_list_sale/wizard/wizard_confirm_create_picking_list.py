# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class WizardConfirmPickingList(models.TransientModel):
    _name = 'wizard.confirm.create.picking.list'
    _description = "Wizard Confirm Picking List"

    create_picking_list = fields.Many2one(comodel_name = "wizard.create.picking.list", string = "Create Picking List")
    generate_picking_list = fields.Many2one('generate.picking.list', string = "Generate Picking List")
    def action_confirm(self):
        res_id = False
        if self.create_picking_list:
            res_id = self.create_picking_list.create_picking()
        if self.generate_picking_list:
            res_id = self.generate_picking_list.create_picking()
        if res_id:
            if len(res_id) > 1:
                view_mode = "tree,form"
            else:
                view_mode = "form"
                res_id = res_id[0]
            action = {
                'name': 'Picking Lists',
                'type': 'ir.actions.act_window',
                'res_model': 'picking.lists',
                'res_id': res_id,
                'view_mode': view_mode,
                "domain": [("id", "in", res_id)],
                }
            return action