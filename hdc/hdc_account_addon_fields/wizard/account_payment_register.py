# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):
        res = super().action_create_payments()
        return res