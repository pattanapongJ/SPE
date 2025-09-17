# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrExpense(models.Model):
    _name = 'hr.expense'
    _inherit = ['hr.expense', 'bs.base.finance.dimension']

    def _prepare_move_values(self):
        _value = super(HrExpense, self)._prepare_move_values()
        _value.update({
            'finance_dimension_1_id': self.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.finance_dimension_3_id.id
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
                    'finance_dimension_1_id': _expense_id.finance_dimension_1_id.id,
                    'finance_dimension_2_id': _expense_id.finance_dimension_2_id.id,
                    'finance_dimension_3_id': _expense_id.finance_dimension_3_id.id
                })

        return move_line_values_by_expense

    def action_move_create(self):
        self._check_required_dimensions()
        return super(HrExpense, self).action_move_create()

    def _check_required_dimensions(self):
        for expense in self.filtered(lambda x: x.state not in ['done', 'refused']):
            _dimension1 = self.env.ref('bs_finance_dimension.bs_dimension_1', raise_if_not_found=False)
            _dimension2 = self.env.ref('bs_finance_dimension.bs_dimension_2', raise_if_not_found=False)
            _dimension3 = self.env.ref('bs_finance_dimension.bs_dimension_3', raise_if_not_found=False)
            if expense.account_id.need_finance_dimension_1 and not expense.finance_dimension_1_id:
                raise ValidationError(_('%s is required.', _dimension1.name if _dimension1 else 'Dimension 1'))
            if expense.account_id.need_finance_dimension_2 and not expense.finance_dimension_2_id:
                raise ValidationError(_('%s is required.', _dimension2.name if _dimension2 else 'Dimension 2'))
            if expense.account_id.need_finance_dimension_3 and not expense.finance_dimension_3_id:
                raise ValidationError(_('%s is required.', _dimension3.name if _dimension3 else 'Dimension 3'))
