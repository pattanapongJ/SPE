# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ShExpense(models.Model):
    _inherit = 'hr.expense'

    @api.model
    def default_cost_center(self):
        if self.env.user.sh_cost_center_id:
            return self.env.user.sh_cost_center_id.id
        return False

    sh_cost_center_id = fields.Many2one(
        'sh.cost.center',
        string="Cost Center",
        default=default_cost_center
    )
