# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
import re

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    incoterm_id = fields.Many2one(comodel_name="account.incoterms", string="Incoterm")

    @api.onchange('partner_id')
    def onchange_partner_id_incoterm_id(self):
        values = { }
        self.incoterm_id = False
        if self.partner_id.sale_incoterm_id:
            values['incoterm_id'] = self.partner_id.sale_incoterm_id
        self.update(values)