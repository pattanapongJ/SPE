from odoo import api, fields, models
from odoo.exceptions import ValidationError

import re

def custom_sanitize_account_number(acc_number, account_holder=None, bank=None):
    if acc_number:
        a_no = re.sub(r'\W+', '', acc_number).upper()
        final_no = a_no + (f"-({account_holder})" if account_holder else "") + (f"[{bank}]" if bank else "")
        return final_no
    return False

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    
    company_id = fields.Many2one(
        'res.company', 'Company', 
        default=lambda self: self.env.company,
        ondelete='set null', readonly=False,
        required=False, 
        company_dependent=True, 
        domain="['|', ('id', '=', current_company_id), ('id', '=', False)]"
    )
    current_company_id = fields.Many2one(
        comodel_name='res.company',
        string='Current Company',
        default=lambda self: self.env.company,
        store=False
    )

    @api.depends('acc_number', 'partner_id', 'bank_bic')
    def _compute_sanitized_acc_number(self):
        for bank in self:
            bank.sanitized_acc_number = custom_sanitize_account_number(
                bank.acc_number, 
                bank.partner_id.id, 
                bank.bank_bic
            )
            
    @api.constrains('acc_number', 'partner_id', 'bank_id', 'company_id')
    def _check_account_number_uniqueness(self):
        """
        Enforce uniqueness of acc_number in combination with partner_id and bank_id.
        """
        for bank in self:
            if not bank.acc_number:
                raise ValidationError("Bank account number cannot be empty.")

            if bank.partner_id and bank.acc_number:
                domain = [
                    ('sanitized_acc_number', '=', bank.sanitized_acc_number),
                    ('id', '!=', bank.id),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        f"Account Number must be unique"
                    )