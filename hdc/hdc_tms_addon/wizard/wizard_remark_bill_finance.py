
from odoo import models, fields

class WizardRemarkBillFinance(models.TransientModel):
    _name = 'wizard.remark.bill.finance'
    _description = 'Wizard to remark bill finance'

    remark_billing = fields.Text("Remark Billing Finance")
    invoice_ids = fields.Many2many('account.move', string="Invoices")

    def remark_bill_finance(self):
        for record in self.invoice_ids:
            record.remark_billing = self.remark_billing

    def action_remark_billing(self):
        active_ids = self.env.context.get('active_ids', [])
        return {
            'name': 'Remark Billing Finance',
            'res_model': 'wizard.remark.bill.finance',
            'view_mode': 'form',
            'view_id': self.env.ref('hdc_tms_addon.wizard_remark_bill_finance_view').id,
            'context': {
                'default_invoice_ids': [(6, 0, active_ids)],
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }