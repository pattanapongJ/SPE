# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_transfer = fields.Boolean(string='Transfer')
    is_cr_return_goods = fields.Boolean(string='Credit Note-Return Goods')