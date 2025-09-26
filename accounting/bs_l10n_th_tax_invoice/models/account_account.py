from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    is_tax_account = fields.Boolean(
        "Is Tax Account",
        default=False,
        help="Check this box if this account is used for tax basic.",
    )
