# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountAccount(models.Model):
    _inherit = 'account.account'

    need_finance_dimension_1 = fields.Boolean(string=_('Need Dimension 1'), default=False)
    need_finance_dimension_2 = fields.Boolean(string=_('Need Dimension 2'), default=False)
    need_finance_dimension_3 = fields.Boolean(string=_('Need Dimension 3'), default=False)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)
        _dimension1 = self.env.ref('bs_finance_dimension.bs_dimension_1', raise_if_not_found=False)
        _dimension2 = self.env.ref('bs_finance_dimension.bs_dimension_2', raise_if_not_found=False)
        _dimension3 = self.env.ref('bs_finance_dimension.bs_dimension_3', raise_if_not_found=False)
        if res.get('need_finance_dimension_1') and _dimension1:
            res['need_finance_dimension_1']['string'] = f'Need {_dimension1.name}'
        if res.get('need_finance_dimension_2') and _dimension2:
            res['need_finance_dimension_2']['string'] =f'Need {_dimension2.name}'
        if res.get('need_finance_dimension_3') and _dimension3:
            res['need_finance_dimension_3']['string'] = f'Need {_dimension3.name}'
        return res
