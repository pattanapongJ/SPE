# Copyright 2020 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import json

from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    firstname_en = fields.Char(string='First Name (EN)')
    lastname_en = fields.Char(string='Last Name (EN)')
    fullname_en = fields.Char(string='Full Name (EN)', compute='_compute_fullname_en', store=True)

    @api.depends('firstname_en', 'lastname_en')
    def _compute_fullname_en(self):
        for rec in self:
            names = [rec.firstname_en or '', rec.lastname_en or '']
            rec.fullname_en = ' '.join(part for part in names if part).strip()
