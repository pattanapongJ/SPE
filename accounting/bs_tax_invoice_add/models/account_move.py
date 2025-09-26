from odoo import models,fields, api,_

class AccountMoveTaxInvoice(models.Model):
    _inherit = 'account.move.tax.invoice'
    
    tax_id = fields.Many2one(comodel_name='account.tax', string='Taxes') 
    
    def write(self, vals):
        if 'tax_id' not in vals:
            for rec in self:
                move_line = self.env['account.move.line'].search([('id', '=', rec.move_line_id.id)])
                if move_line:
                    vals['tax_id'] = move_line.tax_line_id.id if move_line.tax_line_id else False
  
        return super(AccountMoveTaxInvoice, self).write(vals)
    
    
        
    
            
    
    