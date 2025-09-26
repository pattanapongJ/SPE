# -*- coding: utf-8 -*-
import json
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree


_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('move_type')
    def onchange_move_type(self):
        _domain = []
        if self.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
            _domain = [('show_in_sale', '=', True)]
        elif self.move_type in ['in_invoice', 'in_refund', 'in_receipt']:
            _domain = [('show_in_purchase', '=', True)]
        return {'domain': {'currency_id': _domain}}




