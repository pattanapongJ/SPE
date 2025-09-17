from odoo import models, fields,_, api
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_compare


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    
    settle_line_ids = fields.One2many('group.payment.settle','payment_register_id',string='Settle Lines')
    total_settle_amount = fields.Monetary(string='Total Settle Amount',compute='_compute_total_settle_amount')
    has_settle_lines = fields.Boolean(compute='_compute_total_settle_amount')
    show_group_payment_different= fields.Boolean(compute='_compute_show_group_payment_different')
    
    
    
    @api.model
    def prepare_group_payment_settle(self, move):
        """Prepare values for group payment settle line"""
        return {
            'move_id': move.id,
            'settle_amount': move.amount_residual,
        }
        
    @api.onchange('group_payment')
    def onchange_group_payment(self):
        self.settle_line_ids = [(5, 0, 0)]
        if self.group_payment:
            moves = self.line_ids.move_id
            if len(moves) > 1:
                self.settle_line_ids = [(0, 0, self.prepare_group_payment_settle(move)) for move in moves.sorted('invoice_date_due')]

    @api.depends('settle_line_ids.settle_amount')
    def _compute_total_settle_amount(self):
        for record in self:
            record.has_settle_lines = bool(record.settle_line_ids)
            total = sum(line.settle_amount for line in record.settle_line_ids)
            record.total_settle_amount = total
            
    @api.depends('settle_line_ids','can_edit_wizard','can_group_payments','payment_difference')
    def _compute_show_group_payment_different(self):
        for record in self:
            # Implementing the condition:
            # invisible when:
            # 1. payment_difference = 0.0 OR
            # 2. can_edit_wizard = False OR
            # 3. (can_group_payments = True AND group_payment = False)
            
            condition1 = record.payment_difference == 0.0
            condition2 = not record.can_edit_wizard
            condition3 = record.can_group_payments and not record.group_payment
            
            record.show_group_payment_different = not (condition1 or condition2 or condition3) if not record.settle_line_ids else True
           
    
    
    def _compute_from_lines(self):
        res = super()._compute_from_lines()
        for record in self:
            if not record.can_edit_wizard:
                record.settle_line_ids = False
        return res
    
    
    def _reconcile_payments(self, to_process, edit_mode=False):
        if not self.has_settle_lines or self.payment_difference_handling =='reconcile':
            return super()._reconcile_payments(to_process, edit_mode)
        
        RECONCILE_DOMAIN = [
            ('parent_state', '=', 'posted'),
            ('account_internal_type', 'in', ('receivable', 'payable')),
            ('reconciled', '=', False),
        ]
        for vals in to_process:
            payment_lines = vals['payment'].line_ids.filtered_domain(RECONCILE_DOMAIN)
            move_lines = vals['to_reconcile']

            for account in payment_lines.account_id:
                account_domain = [('account_id', '=', account.id), ('reconciled', '=', False)]
                account_payment_lines = payment_lines.filtered_domain(account_domain)
                for settle_line in self.settle_line_ids:
                    if not settle_line.settle_amount:
                        continue
                    settle_move_lines = move_lines.filtered(lambda l: l.move_id == settle_line.move_id)
                    reconcilable_lines = settle_move_lines.filtered_domain(account_domain)
                    
                    if not reconcilable_lines or not account_payment_lines:
                        continue
                    if self.currency_id.is_zero(settle_line.balance):
                        # Full reconciliation
                        (reconcilable_lines + account_payment_lines).reconcile()
                    else:
                        # Partial reconciliation
                        is_invoice = settle_line.move_id.move_type in ('out_invoice', 'out_refund')
                        debit_id = reconcilable_lines.id if is_invoice else account_payment_lines.id
                        credit_id = account_payment_lines.id if is_invoice else reconcilable_lines.id
                        amount = abs(settle_line.settle_amount)
                        
                        partial = self.env['account.partial.reconcile'].create({
                            'amount': amount,
                            'debit_amount_currency': amount,
                            'credit_amount_currency': amount,
                            'debit_move_id': debit_id,
                            'credit_move_id': credit_id
                        })
                        account = (partial.debit_move_id|partial.credit_move_id).mapped('account_id')
                        if len(account)>1:
                            raise UserError(_("Entries are not from the same account"))
                        
                        is_cash_basis_needed = account.company_id.tax_exigibility and account.user_type_id.type in ('receivable', 'payable')
                        if is_cash_basis_needed and not self._context.get('move_reverse_cancel'):
                            tax_cash_basis_moves = partial._create_tax_cash_basis_moves()


                    
                    

    def action_create_payments(self):
        self._check_settle_balance()
        # self._check_settle_amount()
        return super().action_create_payments()
    
    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        if (
            not self.payment_difference and self.has_settle_lines
            and self.payment_difference_handling == "reconcile_multi_deduct"
        ):
            self.with_context({"test": 2})
            payment_vals["write_off_line_vals"] = [
                self._prepare_deduct_move_line(deduct)
                for deduct in self.deduction_ids.filtered(lambda l: not l.open)
            ]
        return payment_vals
    
    
    def _check_settle_balance(self):
        self.ensure_one()
        if not self.has_settle_lines or self.payment_difference_handling == 'reconcile':
            return
        total_balance = sum(line.balance for line in self.settle_line_ids)
        if self.payment_difference_handling == 'open':
            opened_balance = self.payment_difference
        else:
            opened_deductions = self.deduction_ids.filtered(lambda l: l.open)
            opened_balance = sum(opened_deductions.mapped('amount'))
        prec_digits = self.currency_id.decimal_places
        if float_compare(total_balance, opened_balance, precision_digits=prec_digits) != 0:
            raise UserError("Recheck Settle Balance and Open Balance")
        
    
    
    def _check_settle_amount(self):
        self.ensure_one()

        if not (self.has_settle_lines and self.payment_difference_handling == "reconcile_multi_deduct"):
            return

        # Get the precision for the currency
        prec_digits = self.currency_id.decimal_places

        # Filter and calculate amounts for opened and closed deduction lines
        opened_deductions = self.deduction_ids.filtered(lambda l: l.open)
        closed_deductions = self.deduction_ids.filtered(lambda l: not l.open)

        opened_deductions_amount = sum(opened_deductions.mapped('amount'))
        closed_deductions_amount = sum(closed_deductions.mapped('amount'))

        # Calculate total due amount from settle lines
        total_due_amount = sum(line.due_amount for line in self.settle_line_ids)
        total_settle_amount = sum(line.settle_amount for line in self.settle_line_ids)
        
        

        # Calculate the remaining amount after deductions
        remaining_amount = total_due_amount - self.amount - closed_deductions_amount

        # Compare the remaining amount with the opened deductions amount
        if float_compare(remaining_amount, opened_deductions_amount, precision_digits=prec_digits) != 0:
            raise UserError(
                'The total settle amount does not match the payment amount. '
                'Please ensure that the total settle amount equals the payment amount after deductions.'
            )           
        