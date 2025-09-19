from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    wt_document_type = fields.Char(
        string="Withholding Doc Type",
        compute="_compute_wt_document_type",
        store=False,
        readonly=True,
    )

    @api.depends('move_type')
    def _compute_wt_document_type(self):
        for move in self:
            if move.is_sale_document(include_receipts=True):
                move.wt_document_type = 'sale'
            elif move.is_purchase_document(include_receipts=True):
                move.wt_document_type = 'purchase'
            else:
                move.wt_document_type = False
