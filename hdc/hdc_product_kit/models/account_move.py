# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_component = fields.Boolean('is component',default=False)
