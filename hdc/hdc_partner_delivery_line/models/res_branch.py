from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResBranch(models.Model):
    _inherit = 'res.branch'

    choose_only_one = fields.Boolean("Choose Only One")
    
    def write(self, vals):
        if vals.get('choose_only_one'):
            search_branch = self.env['stock.warehouse'].search([('branch_id', '=', self.id)])
            if search_branch:
                if len(search_branch) > 1:
                    raise UserError(_("Unable to active (choose only one) because there are many warehouse choosing this branch."))
        return super(ResBranch, self).write(vals)