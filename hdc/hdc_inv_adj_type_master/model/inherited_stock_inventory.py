# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import MissingError, UserError, ValidationError

class Inventory(models.Model):
    _inherit = 'stock.inventory'

    type_master_id = fields.Many2one(
        'inventory.adjustment.type',
        string='Inventory Adjustment Type',
        help='Select the type of inventory adjustment for this inventory.'
    )

    @api.onchange('type_master_id')
    def _onchange_type_master_id(self):
        if self.type_master_id.type_action:
            self.type_action = self.type_master_id.type_action
        else:
            self.type_action = False

        if self.type_master_id.name:
            self.name = self.type_master_id.name

    @api.model
    def create(self, vals):
        sequence = vals.get('sequence', 'New')
        if sequence:
            if vals.get("type_master_id"):
                type_master = self.env['inventory.adjustment.type'].browse(vals["type_master_id"])
                if type_master and type_master.sequence_id:
                    vals['sequence'] = type_master.sequence_id.next_by_code('inventory_adjustment') or _('New')
                else:
                    vals['sequence'] = self.env['ir.sequence'].next_by_code('inventory_adjustment') or _('New')
            else:
                vals['sequence'] = self.env['ir.sequence'].next_by_code('inventory_adjustment') or _('New')

        result = super(Inventory, self).create(vals)
        return result


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"