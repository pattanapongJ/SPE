# Copyright 2020 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import json

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    # access_right = fields.Selection(
    #     [('all', 'Admin Picking List'),
    #      ('confirm', 'Confirm Picking Qty'),
    #      ('validate', 'Validate Picking Done')],
    #     string='Access Right'
    # )

    # def get_access_groups(self):
    #     groups = {
    #         'all': 'hdc_picking_list_access_right.group_all',
    #         'confirm': 'hdc_picking_list_access_right.group_confirm',
    #         'validate': 'hdc_picking_list_access_right.group_validate',
    #     }
    #     return groups.get(self.access_right, 'hdc_picking_list_access_right.group_all')