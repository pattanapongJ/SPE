# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields


class ShResUsers(models.Model):
    _inherit = 'res.users'

    sh_cost_center_id = fields.Many2one(
        'sh.cost.center',
        string="Cost Center"
    )
