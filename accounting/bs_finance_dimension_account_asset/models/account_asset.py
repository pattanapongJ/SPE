from odoo import api, fields, models


class AccountAsset(models.Model):
    _name = 'account.asset'
    _inherit = ['account.asset', 'bs.base.finance.dimension']


class AccountAssetLine(models.Model):
    _inherit = 'account.asset.line'

    def _setup_move_data(self, depreciation_date):
        _value = super()._setup_move_data(depreciation_date)
        _assset = self.asset_id
        _value.update({
            'finance_dimension_1_id': _assset.finance_dimension_1_id.id,
            'finance_dimension_2_id': _assset.finance_dimension_2_id.id,
            'finance_dimension_3_id': _assset.finance_dimension_3_id.id
        })
        return _value

    def _setup_move_line_data(self, depreciation_date, account, ml_type, move):
        _value = super(AccountAssetLine, self)._setup_move_line_data(depreciation_date, account, ml_type, move)
        _assset = self.asset_id
        _value.update({
            'finance_dimension_1_id': _assset.finance_dimension_1_id.id,
            'finance_dimension_2_id': _assset.finance_dimension_2_id.id,
            'finance_dimension_3_id': _assset.finance_dimension_3_id.id
        })
        return _value


class AccountAssetRemove(models.TransientModel):
    _inherit = 'account.asset.remove'

    def _get_removal_data(self, asset, residual_value):
        move_lines = super(AccountAssetRemove, self)._get_removal_data(asset, residual_value)
        for line in move_lines:
            line[2].update({
                'finance_dimension_1_id': asset.finance_dimension_1_id.id,
                'finance_dimension_2_id': asset.finance_dimension_2_id.id,
                'finance_dimension_3_id': asset.finance_dimension_3_id.id
            })

        return move_lines
