from odoo import api, fields, models

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    
    payment_label = fields.Char(string='Label', compute='_compute_payment_label', readonly=False)
    
    @api.depends('partner_id', 'cheque_ref', 'payment_method_id')
    def _compute_payment_label(self):
        try:
            method_label = self.payment_method_id.payment_label if self.payment_method_id.payment_label else ''
            cheque_ref = self.cheque_ref if self.cheque_ref else ''
            partner_ref = self.partner_id.ref if self.partner_id.ref else ''
            partner_name = self.partner_id.name if self.partner_id.name else ''
            
            self.payment_label = f'{method_label}: {partner_ref} {partner_name} {cheque_ref}'
        except Exception:
            return
        
    def _init_payments(self, to_process, edit_mode=False):
        payments = super()._init_payments(to_process, edit_mode)
        
        for line in payments.line_ids:
            line.write({'name': self.payment_label})
        
        return payments

    @api.model
    def _get_deduction_ids_context(self, existing_context):
        context = super(AccountPaymentRegister, self)._get_deduction_ids_context(existing_context)
        context.update({
            'default_name': 'payment_label'
        })
        return context
    
    @api.depends('can_edit_wizard')
    def _compute_communication(self):
        if self.payment_label:
            self.communication = self.payment_label
        else:
            return super(AccountPaymentRegister, self)._compute_communication()