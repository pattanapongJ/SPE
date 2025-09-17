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

    bl_awb_no = fields.Char("BL, AWB No.", tracking = True,)
    bl_awb_no_date = fields.Date("BL, AWB No. Date", tracking = True,)
    import_declaration_no = fields.Char("Import Declaration No.", tracking = True,)
    import_declaration_no_date = fields.Date("Import Declaration No. Date", tracking = True,)
    duty_payment_no = fields.Char("Duty Payment No.", tracking = True,)
    duty_payment_no_date = fields.Date("Duty Payment No. Date", tracking = True,)
    edt_form_no = fields.Char("E/D/T Form No.", tracking = True,)
    edt_form_no_date = fields.Date("E/D/T Form No. Date", tracking = True,)

    shipper = fields.Char(string="Shipper")

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    