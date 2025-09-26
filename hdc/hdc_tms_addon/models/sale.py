# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _order = 'priority desc, id desc'

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.delivery_trl:
            res["transport_line_id"] = self.delivery_trl.id
        if self.delivery_trl_description:
            res["transport_desc"] = self.delivery_trl_description
        if self.delivery_company:
            res["company_round_id"] = self.delivery_company.id
        if self.delivery_company_description:
            res["company_round_desc"] = self.delivery_company_description
        return res
