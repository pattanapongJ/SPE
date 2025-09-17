from odoo import api, fields, models, _
import re


class AccountMove(models.Model):
    _inherit = "account.move"

    document_stamp_state_id = fields.Many2one(
        'document.stamp.state',
        string='Document Stamp State',
        help="The state of the document stamp for this move.",
    )
