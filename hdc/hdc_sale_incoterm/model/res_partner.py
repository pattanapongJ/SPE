# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sale_incoterm_id = fields.Many2one(
        comodel_name="account.incoterms",
        ondelete="restrict",
        string="Default Sale Order Incoterm",
    )
