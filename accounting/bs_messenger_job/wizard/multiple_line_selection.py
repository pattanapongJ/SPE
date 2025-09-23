# -*- encoding: utf-8 -*-
from odoo import api, fields, models

class MultipleLineSelection(models.TransientModel):
    _name = 'multi.selection.wizard'
    _description = 'Multiple Line Selection'

    messenger_job_id = fields.Many2one('messenger.job', string='Messenger Job')
    batch_line_ids = fields.Many2many('batch.billing.line', string='Billing Lines', domain=[('batch_billing_id.state', '=', 'done'), ('done_job', '=', False)])

    def action_add_lines(self):
        self.ensure_one()
        
        active_id = self.env.context.get('active_id')
        messenger_job = self.messenger_job_id or self.env['messenger.job'].browse(active_id)
        
        if not messenger_job or messenger_job.state != 'draft':
            raise ValueError("Messenger Job not found or not in draft state.")
        if not self.batch_line_ids:
            raise ValueError("No billing lines selected.")
        
        lines_to_add = []
        existing_lines = messenger_job.line_ids.mapped('batch_billing_line_id').ids
        for line in self.batch_line_ids:
            if line.id not in existing_lines:
                lines_to_add.append((0, 0, {
                    'batch_billing_line_id': line.id,
                }))

        messenger_job.line_ids = lines_to_add
        return {'type': 'ir.actions.act_window_close'}        