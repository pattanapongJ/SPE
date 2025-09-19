# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    show_in_credit_note = fields.Boolean(
        string='Show In Credit Note')
    show_in_debit_note = fields.Boolean(
        string='Show In Debit Note')
    is_m = fields.Boolean(string='M',default=True)
    is_g = fields.Boolean(string='G',default=True)

