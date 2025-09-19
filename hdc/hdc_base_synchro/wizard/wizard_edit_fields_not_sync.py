# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class WizardEditFieldsNotSync(models.TransientModel):
    _name = 'wizard.edit.fields.not.sync'
    _description = "Wizard to edit fields not sync"

    obj_id = fields.Many2one("base.synchro.obj", "Object")
    wizard_edit_fields_not_sync_line = fields.One2many(
        comodel_name="wizard.edit.fields.not.sync.line",
        inverse_name='wizard_edit_fields_not_sync_id',
        string="Fields Not Sync.",
    )

    def action_edit(self):
        for avoid_id in self.obj_id.avoid_ids:
            avoid_id.unlink()
        avoid_ids = self.env["base.synchro.obj.avoid"]
        for line in self.wizard_edit_fields_not_sync_line:
            if line.selected == True:
                avoid_ids.create({
                        'obj_id': self.obj_id.id,
                        'name': line.name,
                        'field_description': line.field_description,
                        })
        
class WizardEditFieldsNotSyncLine(models.TransientModel):
    _name = 'wizard.edit.fields.not.sync.line'
    _description = "Wizard to edit fields not sync line"

    wizard_edit_fields_not_sync_id = fields.Many2one("wizard.edit.fields.not.sync", "Wizard Edit Field")
    selected = fields.Boolean(string="Select")
    name = fields.Char(string='Field Name')
    field_description = fields.Char(string='Field Label')