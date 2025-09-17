# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    # pdc_journal_checkbox = fields.Boolean(string="PDC Journal")