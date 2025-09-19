# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    note_text = fields.Text()

    def action_confirm(self):
        result = super(SaleOrder, self).action_confirm()
        self.picking_ids[:1].note = self.note_text
        return result
