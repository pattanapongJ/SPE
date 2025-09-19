# Copyright 2022 Basic Solution Co.,Ltd. <warat.m@basic-solution.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    contact_person = fields.Char()
