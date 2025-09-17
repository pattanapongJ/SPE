from odoo import models, fields

class DebitCreditNoteReason(models.Model):
    _name = "debit.credit.note.reason"
    _description = "Debit and Credit Note Reason"

    name = fields.Char(string="Reason", required=True)
    type = fields.Selection([
        ('debit', 'Debit Note'),
        ('credit', 'Credit Note'),
    ], string="Type", required=True)
