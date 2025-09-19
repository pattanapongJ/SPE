from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    @api.model
    def create(self, vals):
        if vals.get('branch_id'):
            search_branch = self.env['res.branch'].search([('id', '=', vals['branch_id']),('choose_only_one', '=', True)])
            if search_branch:
                raise UserError(_("Unable to select a branch because this branch can only select one warehouse."))
        return super(StockWarehouse, self).create(vals)
    
    def write(self, vals):
        if vals.get('branch_id'):
            search_branch = self.env['res.branch'].search([('id', '=', vals['branch_id']),('choose_only_one', '=', True)])
            if search_branch:
                raise UserError(_("Unable to select a branch because this branch can only select one warehouse."))
        return super(StockWarehouse, self).write(vals)