# -*- coding: utf-8 -*-
import base64
import io
from odoo import models, fields, api

class WizardAddLine(models.TransientModel):
    _name = "wizard.add.invoice.line"
    _description = "HDC Wizard Batch Line"

    batch_billing_id = fields.Many2one('batch.billing', string='Batch Billing Reference')
    company_id = fields.Many2one('res.company', string='Company')
    invoice_exclude_ids = fields.Many2many(
        related='batch_billing_id.invoice_exclude_ids',
    )

    invoice_ids = fields.Many2many(
        'account.move',
        string='Invoice No.',
        domain="[('move_type', 'in', ['out_invoice', 'out_refund']), "
               "('state', '=', 'posted'), "
               "('payment_state', 'in', ['not_paid', 'partial']), "
               "('id', 'not in', invoice_exclude_ids)]"
    )

    def action_add_invoice_line(self):      
        self.ensure_one()
        picking = self.batch_billing_id

        existing_invoice_ids = picking.line_ids.mapped('invoice_id.id')

        move_lines = []
        for billing in self.invoice_ids:
            if billing.id not in existing_invoice_ids:
                move_line_vals = {
                    'invoice_id': billing.id,
                    'billing_no': billing.name,
                }
                move_lines.append((0, 0, move_line_vals))

        if move_lines:
            picking.write({
                'line_ids': move_lines,
            })

        return {'type': 'ir.actions.act_window_close'}
