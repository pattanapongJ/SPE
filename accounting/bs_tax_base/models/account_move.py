from odoo import api,models,_
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"
    
    @api.onchange('manual_currency_rate_active', 'manual_currency_inverse_rate', 'invoice_line_ids')
    def on_change_currency(self):
        invoices = self.filtered(lambda x: x.state == "draft").with_context(
            check_move_validity=False,
        )
        for invoice in invoices:
            to_currency = invoice.currency_id
            if invoice.manual_currency_rate_active and invoice.manual_currency_rate:
                context = {"custom_rate": invoice.manual_currency_rate, "to_currency": to_currency}
                invoice = invoice.with_context(**context)
            
                invoice._recompute_dynamic_lines(recompute_all_taxes=True)
                
    def action_update_currency(self):
        invoices = self.filtered(lambda x: x.state == "draft").with_context(
            check_move_validity=False,
        )
        for invoice in invoices:
            to_currency = invoice.currency_id
            if invoice.manual_currency_rate_active and invoice.manual_currency_rate:
                context = {
                    "custom_rate": invoice.manual_currency_rate, 
                    "to_currency": to_currency,
                
                }
                invoice = invoice.with_context(**context)
            
                invoice._recompute_dynamic_lines(recompute_all_taxes=True)
                
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        move = super(AccountMove, self).copy(default)
        invoices = move.filtered(lambda x: x.state == "draft").with_context(
            check_move_validity=False,
        )
        for invoice in invoices:
            to_currency = invoice.currency_id
            if invoice.manual_currency_rate_active and invoice.manual_currency_rate:
                context = {
                    "custom_rate": invoice.manual_currency_rate, 
                    "to_currency": to_currency,
                }
                invoice = invoice.with_context(**context)
            
                invoice._recompute_dynamic_lines(recompute_all_taxes=True)
        return invoices
                
    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        if any('state' in vals and vals.get('state') == 'posted' for vals in vals_list):
            raise UserError(_('You cannot create a move already in the posted state. Please create a draft move and post it after.'))

        vals_list = self._move_autocomplete_invoice_lines_create(vals_list)
        rslt = super(AccountMove, self).create(vals_list)
        rslt.action_update_currency()
        for i, vals in enumerate(vals_list):
            if 'line_ids' in vals:
                rslt[i].update_lines_tax_exigibility()
        return rslt
                
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    def write(self, vals):
        
        result = super(AccountMoveLine, self).write(vals)
             
        if 'tax_base_amount' in vals:
            for line in self:
                taxinv = line.tax_invoice_ids
                if taxinv:
                    taxinv.write(
                    {
                        "move_id": line.move_id.id,
                        "move_line_id": line.id,
                        "partner_id": line.partner_id.id,
                        "tax_base_amount": abs(line.tax_base_amount),
                        "balance": abs(line.balance),
                    }
                )
                line.tax_invoice_ids |= taxinv
                    
        return result

    
        
    
            
            
    