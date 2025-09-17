# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from collections import defaultdict
import re

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    incoterm_id = fields.Many2one(comodel_name="account.incoterms", string="Incoterm")
    
    @api.onchange('partner_id')
    def onchange_partner_id_incoterm_id(self):
        if self.ref_sale_id:
            return
        values = { }
        self.incoterm_id = False
        if self.partner_id.sale_incoterm_id:
            values['incoterm_id'] = self.partner_id.sale_incoterm_id
        self.update(values)