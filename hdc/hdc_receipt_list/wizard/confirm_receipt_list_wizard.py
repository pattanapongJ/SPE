# -*- coding: utf-8 -*-
from odoo import _, api, fields, models

class ConfirmReceiptListWizard(models.TransientModel):
    _name = 'confirm.receipt.list.wizard'
    _description = 'Confirm Receipt List Wizard'

    receipt_list_id = fields.Many2one('receipt.list', string='Receipt List')

    def confirm_backorder(self):
        return self.receipt_list_id.with_context(confirm_backorder=True).confirm_validate()
        
    def confirm_cancel(self):
        return self.receipt_list_id.confirm_validate()