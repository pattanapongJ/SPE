# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import re

class AccountMove(models.Model):
    _inherit = "account.move"

    debit_credit_note_reason_id = fields.Many2one('debit.credit.note.reason', string="Debit,Credit Note Reason")

