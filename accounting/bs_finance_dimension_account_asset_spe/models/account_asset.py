# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAssetLine(models.Model):
    _inherit = 'account.asset.line'

    def _setup_move_data(self, depreciation_date):
        _value = super()._setup_move_data(depreciation_date)
        _assset = self.asset_id
        _value.update({
            'finance_dimension_4_id': _assset.finance_dimension_4_id.id,
            'finance_dimension_5_id': _assset.finance_dimension_5_id.id,
            'finance_dimension_6_id': _assset.finance_dimension_6_id.id,
            'finance_dimension_7_id': _assset.finance_dimension_7_id.id,
            'finance_dimension_8_id': _assset.finance_dimension_8_id.id,
            'finance_dimension_9_id': _assset.finance_dimension_9_id.id,
            'finance_dimension_10_id': _assset.finance_dimension_10_id.id
        })
        return _value

    def _setup_move_line_data(self, depreciation_date, account, ml_type, move):
        _value = super(AccountAssetLine, self)._setup_move_line_data(depreciation_date, account, ml_type, move)
        _assset = self.asset_id
        _value.update({
            'finance_dimension_4_id': _assset.finance_dimension_4_id.id,
            'finance_dimension_5_id': _assset.finance_dimension_5_id.id,
            'finance_dimension_6_id': _assset.finance_dimension_6_id.id,
            'finance_dimension_7_id': _assset.finance_dimension_7_id.id,
            'finance_dimension_8_id': _assset.finance_dimension_8_id.id,
            'finance_dimension_9_id': _assset.finance_dimension_9_id.id,
            'finance_dimension_10_id': _assset.finance_dimension_10_id.id
        })
        return _value


class AccountAssetRemove(models.TransientModel):
    _inherit = 'account.asset.remove'

    def _get_removal_data(self, asset, residual_value):
        move_lines = super(AccountAssetRemove, self)._get_removal_data(asset, residual_value)
        for line in move_lines:
            line[2].update({
                'finance_dimension_4_id': asset.finance_dimension_4_id.id,
                'finance_dimension_5_id': asset.finance_dimension_5_id.id,
                'finance_dimension_6_id': asset.finance_dimension_6_id.id,
                'finance_dimension_7_id': asset.finance_dimension_7_id.id,
                'finance_dimension_8_id': asset.finance_dimension_8_id.id,
                'finance_dimension_9_id': asset.finance_dimension_9_id.id,
                'finance_dimension_10_id': asset.finance_dimension_10_id.id
            })

        return move_lines
