'''
Created on Nov 12, 2020

@author: Zuhair Hammadi
'''
from odoo import models, _
from odoo.exceptions import UserError

class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"
        
    def action_view_lines(self):
        ref = lambda name : self.env.ref(name).id
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Transactions'),
            'res_model' : 'account.bank.statement.line',
            'view_mode' : 'tree,form',
            'views' : [(ref('oi_bank_reconciliation.view_bank_statement_line_tree_reconciliation'), 'tree'), 
                       (ref('oi_bank_reconciliation.view_bank_statement_line_form_reconciliation'), 'form')
                       ],
            'domain' : [('statement_id','=', self.id)],
            'context' : {
                'default_statement_id' : self.id
                }
            }
                
    def action_transaction_generate(self):
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Generate Transactions'),
            'res_model' : 'account.bank.statement.generate',
            'view_mode' : 'form',
            'target' : 'new',
            'context' : {
                'default_statement_id' : self.id,                
                }   
            }
        
    def action_reconcile(self, line_id = None):
        line_ids = self.line_ids
        
        if line_id is not None:
            index = line_ids.ids.index(line_id.id)
            line_ids = line_ids[index + 1:]
        
        for line in line_ids:                            
            if not line.is_reconciled:
                try:
                    line.action_reconcile()
                except UserError:
                    return line.with_context(reconcile_all_line = True).button_reconciliation()
                
    def auto_balance_end(self):
        self.balance_end_real = self.balance_end