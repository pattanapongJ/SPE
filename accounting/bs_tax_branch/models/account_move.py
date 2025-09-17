from odoo import api, fields, models,_

class AccountMoveTaxInvoice(models.Model):
    _inherit = "account.move.tax.invoice"
    
    branch_id = fields.Many2one('res.branch', string='Branch', readonly=True)

class AccountMove(models.Model):
    _inherit = "account.move"
    
    def write(self, vals):
        result = super(AccountMove, self).write(vals)
      
        if 'branch_id' in vals:
            for line in self:
                taxinv = line.tax_invoice_ids
                if taxinv:
                    taxinv.write(
                    {
                        "branch_id": line.branch_id.id
                    }
                )
                    
        return result
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    @api.model_create_multi
    def create(self, vals_list):
        move_lines = super().create(vals_list)

        for line in move_lines:
            if line.tax_invoice_ids:
                line.tax_invoice_ids.write(
                    {
                        "branch_id": line.branch_id.id
                    }
                )

        return move_lines
    
class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    def _create_tax_cash_basis_moves(self):
        """This method is called from the move lines that
        create cash basis entry. We want to use the same payment_id when
        create account.move.tax.invoice"""
        move_lines = super()._create_tax_cash_basis_moves()
        move_lines.update({
            "branch_id": move_lines.tax_cash_basis_move_id.branch_id.id
        })
        return move_lines