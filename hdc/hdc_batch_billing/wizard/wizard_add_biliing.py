# -*- coding: utf-8 -*-
import base64
import io
from odoo import models, fields, api

class WizardAddBilling(models.TransientModel):
    _name = "wizard.add.billing"
    _description = "HDC Wizard Batch Billing"

    account_billing = fields.Many2one('account.billing', string='Billing ID')
    batch_billing_id = fields.Many2one('batch.billing', string='Batch Billing Reference')
    company_id = fields.Many2one('res.company', string='Company')
    billing_ids = fields.Many2many('account.billing', string='Billing', 
                                   domain="[('batch_billing_status', '=', 'wait'), ('bill_type', '=', 'out_invoice'), ('state', '=', 'billed'),('company_id','=',company_id)]")


    def action_add_billing(self):      
        self.ensure_one()
        picking = self.batch_billing_id

        existing_invoice_ids = picking.line_ids.mapped('invoice_id.id')

        move_lines = []
        for billing in self.billing_ids:
            for billing_line in billing.billing_line_ids:
                if billing_line.invoice_id.id not in existing_invoice_ids:
                    move_line_vals = {
                        'invoice_id': billing_line.invoice_id.id,
                        'billing_no': billing.name,
                    }
                    move_lines.append((0, 0, move_line_vals))

        if move_lines:
            picking.write({
                'line_ids': move_lines,
            })

        return {'type': 'ir.actions.act_window_close'}
