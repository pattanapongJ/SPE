from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    partner_ref = fields.Char(
        string="Partner Ref",
        related="partner_id.ref",
        store=True,
        readonly=True,
    )
