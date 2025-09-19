'''
Created on Nov 11, 2020

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountBankStatementLine(models.Model):
    _name = "account.bank.statement.line"
    _inherit = ['account.bank.statement.line', 'mail.thread', 'mail.activity.mixin']

    _rec_name = 'payment_ref'
    
    matched_payment_ids = fields.Many2many('account.payment', relation='bank_statement_line_matched_payment_rel')
    matched_move_line_ids = fields.Many2many('account.move.line', relation='bank_statement_line_matched_move_line')
    matched_manual_ids = fields.One2many('account.bank.statement.manual', 'statement_line_id')
    matched_balance = fields.Monetary(compute = "_calc_matched_balance", string='Open Balance')
    matched_balance_absolute = fields.Monetary(compute = "_calc_matched_balance", string='Open Balance (Absolute)')
    create_payment_for_invoice = fields.Boolean()
    
    reconcile_state = fields.Selection([('Reconciled','Reconciled'),('Unreconciled','Unreconciled')], compute = '_calc_reconcile_state', string="Reconcile Status")
    
    is_reconciled = fields.Boolean(tracking = True)
    amount_residual = fields.Float(tracking = True)
    amount = fields.Monetary(tracking = True)
    
    @api.onchange('matched_manual_ids')
    def _onchange_matched_manual_ids(self, force_update = False):
        in_draft_mode = self != self._origin
        
        def need_update():
            amount = 0
            for line in self.matched_manual_ids:
                if line.auto_tax_line:
                    amount -= line.balance
                    continue
                if line.tax_ids:
                    balance_taxes_res = line.tax_ids._origin.compute_all(
                        line.balance,
                        currency=line.currency_id,
                        quantity=1,
                        product=line.product_id,
                        partner=line.partner_id,
                        is_refund=False,
                        handle_price_include=True,
                    )
                    for tax_res in balance_taxes_res.get("taxes"):
                        amount += tax_res['amount']
            return amount 
        
        if not force_update and not need_update():
            return
        
        to_remove = self.env['account.bank.statement.manual']        
        if self.matched_manual_ids:
            for line in list(self.matched_manual_ids):
                print(line, line.auto_tax_line)
                if line.auto_tax_line:
                    to_remove += line
                    continue
                if line.tax_ids:
                    balance_taxes_res = line.tax_ids._origin.compute_all(
                        line.balance,
                        currency=line.currency_id,
                        quantity=1,
                        product=line.product_id,
                        partner=line.partner_id,
                        is_refund=False,
                        handle_price_include=True,
                    )
                    for tax_res in balance_taxes_res.get("taxes"):
                        create_method = in_draft_mode and line.new or line.create
                        create_method({
                            'statement_line_id' : self.id,
                            'account_id' : tax_res['account_id'],
                            'name' : tax_res['name'],
                            'balance' : tax_res['amount'],
                            'tax_repartition_line_id' : tax_res['tax_repartition_line_id'],
                            'tax_tag_ids' : tax_res['tag_ids'],
                            'auto_tax_line' : True,
                            'sequence' : line.sequence,
                            'tax_line_id' : line.id
                            })
            
            if in_draft_mode:
                self.matched_manual_ids -=to_remove
            else:
                to_remove.unlink()
    
    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        for vals in vals_list:
            if 'statement_id' not in vals and self._context.get('default_statement_id'):
                vals['statement_id'] = self._context.get('default_statement_id')
                
        return super(AccountBankStatementLine, self).create(vals_list)
    
    @api.depends('is_reconciled')
    def _calc_reconcile_state(self):
        for record in self:
            record.reconcile_state = record.is_reconciled and 'Reconciled' or 'Unreconciled'
    
    def button_reconciliation(self):
        ref = lambda name : self.env.ref(name).id
        context = dict(self._context)
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Reconciliation'),
            'target' : 'new',
            'res_model' : 'account.bank.statement.line',
            'res_id' : self.id,
            'view_mode' : 'form',
            'views' : [(ref('oi_bank_reconciliation.view_bank_statement_line_form_reconciliation_popup'), 'form')], 
            'context' : context           
            }
    
    def _prepare_reconciliation(self, lines_vals_list, create_payment_for_invoice=False):
        if self._context.get("create_payment_for_invoice") is not None:
            create_payment_for_invoice = self._context.get("create_payment_for_invoice")
        
        reconciliation_overview, open_balance_vals = super(AccountBankStatementLine, self)._prepare_reconciliation(lines_vals_list, create_payment_for_invoice = create_payment_for_invoice)
        
        
        for item in reconciliation_overview:
            payment_vals = item.get("payment_vals")
            if payment_vals:
                payment_vals['statement_line_ids'] = [(6,0, self.ids)]
                    
        return reconciliation_overview, open_balance_vals
            
    def _get_reconcile_lines_vals_list(self):
        self.ensure_one()
        lines_vals_list = []
        
        for payment in self.matched_payment_ids:
            liquidity_lines, counterpart_lines, writeoff_lines = payment._seek_for_lines()   # @UnusedVariable             
            for line in liquidity_lines:
                lines_vals_list.append({'id' : line._origin.id})
        
        for line in self.matched_move_line_ids:
            lines_vals_list.append({'id' : line._origin.id})
            
        for line in self.matched_manual_ids:
            vals = {name : line[name] for name in ['account_id','name','balance','partner_id','tax_ids','analytic_account_id','analytic_tag_ids', 'tax_repartition_line_id']}
            vals['balance'] = -vals['balance']
            vals = line._convert_to_write(vals)
            lines_vals_list.append(vals)
                
        return lines_vals_list
    
    def action_reconcile_next(self):
        return self.statement_id.action_reconcile(line_id = self)        
    
    def action_reconcile(self):
        self._onchange_matched_manual_ids(force_update = True)
        
        lines_vals_list = self._get_reconcile_lines_vals_list()
        self.with_context(create_payment_for_invoice = self.create_payment_for_invoice).reconcile(lines_vals_list)
        
        if self._context.get("reconcile_all_line"):
            return self.statement_id.action_reconcile(line_id = self)
        
        
    
    @api.depends('matched_payment_ids','matched_move_line_ids','matched_manual_ids')
    def _calc_matched_balance(self):
        for record in self:
            if not record.id:
                record.matched_balance = 0
                record.matched_balance_absolute = 0
                continue
            try:
                lines_vals_list = record._get_reconcile_lines_vals_list()
                _, open_balance_vals = record._prepare_reconciliation(lines_vals_list, create_payment_for_invoice = record.create_payment_for_invoice)            
                record.matched_balance = open_balance_vals and -open_balance_vals.get("amount_currency")
            except UserError:
                record.matched_balance = 0
            record.matched_balance_absolute = abs(record.matched_balance)
                
            