# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    allow_defer_posting = fields.Boolean(
        related="company_id.allow_defer_posting",
        readonly=False,
        help="If checked, Tax Invoice's Journal Entry will posted automatically like Odoo Workflow"
    )
