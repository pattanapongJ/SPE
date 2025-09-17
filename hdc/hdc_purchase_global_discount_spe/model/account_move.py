# Copyright 2009-2018 Noviat
# Copyright 2021 Tecnativa - João Marques
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests.common import Form

_logger = logging.getLogger(__name__)
class AccountMove(models.Model):
    _inherit = "account.move"

    discount_price = fields.Char("ส่วนลดท้ายบิล", tracking = True,digits='Product Price')

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    gross_unit_price = fields.Float(string = "Unit Price",digits='Product Price')
    net_amount = fields.Float(string = "Net Amount",digits='Product Price',compute='_compute_net_amount')
    
    @api.depends("gross_unit_price", "quantity")
    def _compute_net_amount(self):
        for rec in self:
            net_amount = rec.quantity * rec.price_unit
            rec.net_amount = net_amount

    