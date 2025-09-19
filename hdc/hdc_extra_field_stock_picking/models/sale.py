# -*- coding: utf-8 -*-


import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.tools.float_utils import float_repr
from odoo.tools.misc import format_date
from odoo.exceptions import Warning, ValidationError, UserError, RedirectWarning


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_create_borrow(self):
        result = super(SaleOrder, self).action_create_borrow()

        default_team = self._get_default_team()
        context = result.get("context")
        if context:
            context.update(
                {
                    "default_team_id": default_team.id,
                    "default_partner_id": self.partner_id.id
                }
            )
        if isinstance(result, dict):
            result["context"] = context
        return result