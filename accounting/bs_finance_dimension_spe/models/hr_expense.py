# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    def _prepare_move_values(self):
        _value = super(HrExpense, self)._prepare_move_values()
        _value.update({
            'finance_dimension_4_id': self.finance_dimension_4_id.id,
            'finance_dimension_5_id': self.finance_dimension_5_id.id,
            'finance_dimension_6_id': self.finance_dimension_6_id.id,
            'finance_dimension_7_id': self.finance_dimension_7_id.id,
            'finance_dimension_8_id': self.finance_dimension_8_id.id,
            'finance_dimension_9_id': self.finance_dimension_9_id.id,
            'finance_dimension_10_id': self.finance_dimension_10_id.id
        })
        return _value

    def _get_account_move_line_values(self):
        move_line_values_by_expense = super(HrExpense, self)._get_account_move_line_values()
        for expense, move_lines in move_line_values_by_expense.items():
            _expense_id = self.env['hr.expense'].browse(expense)
            if not _expense_id.exists():
                continue
            for aml in move_lines:
                aml.update({
                    'finance_dimension_4_id': _expense_id.finance_dimension_4_id.id,
                    'finance_dimension_5_id': _expense_id.finance_dimension_5_id.id,
                    'finance_dimension_6_id': _expense_id.finance_dimension_6_id.id,
                    'finance_dimension_7_id': _expense_id.finance_dimension_7_id.id,
                    'finance_dimension_8_id': _expense_id.finance_dimension_8_id.id,
                    'finance_dimension_9_id': _expense_id.finance_dimension_9_id.id,
                    'finance_dimension_10_id': _expense_id.finance_dimension_10_id.id
                })

        return move_line_values_by_expense
    
    def _check_required_dimensions(self):
        super(HrExpense,self)._check_required_dimensions()
        for expense in self.filtered(lambda x: x.state not in ['done', 'refused']):
            _dimension4 = self.env.ref('bs_finance_dimension_spe.bs_dimension_4', raise_if_not_found=False)
            _dimension5 = self.env.ref('bs_finance_dimension_spe.bs_dimension_5', raise_if_not_found=False)
            _dimension6 = self.env.ref('bs_finance_dimension_spe.bs_dimension_6', raise_if_not_found=False)
            _dimension7 = self.env.ref('bs_finance_dimension_spe.bs_dimension_7', raise_if_not_found=False)
            _dimension8 = self.env.ref('bs_finance_dimension_spe.bs_dimension_8', raise_if_not_found=False)
            _dimension9 = self.env.ref('bs_finance_dimension_spe.bs_dimension_9', raise_if_not_found=False)
            _dimension10 = self.env.ref('bs_finance_dimension_spe.bs_dimension_10', raise_if_not_found=False)
            
            
            if expense.account_id.need_finance_dimension_4 and not expense.finance_dimension_4_id:
                raise ValidationError(_('%s is required.', _dimension4.name if _dimension4 else 'Dimension 4'))
            if expense.account_id.need_finance_dimension_5 and not expense.finance_dimension_5_id:
                raise ValidationError(_('%s is required.', _dimension5.name if _dimension5 else 'Dimension 5'))
            if expense.account_id.need_finance_dimension_6 and not expense.finance_dimension_6_id:
                raise ValidationError(_('%s is required.', _dimension6.name if _dimension6 else 'Dimension 6'))
            if expense.account_id.need_finance_dimension_7 and not expense.finance_dimension_7_id:
                raise ValidationError(_('%s is required.', _dimension7.name if _dimension7 else 'Dimension 7'))
            if expense.account_id.need_finance_dimension_8 and not expense.finance_dimension_8_id:
                raise ValidationError(_('%s is required.', _dimension8.name if _dimension8 else 'Dimension 8'))
            if expense.account_id.need_finance_dimension_9 and not expense.finance_dimension_9_id:
                raise ValidationError(_('%s is required.', _dimension9.name if _dimension9 else 'Dimension 9'))
            if expense.account_id.need_finance_dimension_10 and not expense.finance_dimension_10_id:
                raise ValidationError(_('%s is required.', _dimension10.name if _dimension10 else 'Dimension 10'))
            
