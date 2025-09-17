# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    "out_invoice": "customer",
    "in_invoice": "supplier",
}


class AccountBilling(models.Model):
    _inherit = "account.billing"

    form_no = fields.Char(string="Form No.")
    old_spe_billing_no = fields.Char(string="Old SPE Billing No.")

