# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = 'account.account'
    
    
    need_finance_dimension_4 = fields.Boolean(string=_('Need Dimension 4'), default=False)
    need_finance_dimension_5 = fields.Boolean(string=_('Need Dimension 5'), default=False)
    need_finance_dimension_6 = fields.Boolean(string=_('Need Dimension 6'), default=False)
    need_finance_dimension_7 = fields.Boolean(string=_('Need Dimension 7'), default=False)
    need_finance_dimension_8 = fields.Boolean(string=_('Need Dimension 8'), default=False)
    need_finance_dimension_9 = fields.Boolean(string=_('Need Dimension 9'), default=False)
    need_finance_dimension_10 = fields.Boolean(string=_('Need Dimension 10'), default=False)
    
    

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)
        _dimension4 = self.env.ref('bs_finance_dimension_spe.bs_dimension_4', raise_if_not_found=False)
        _dimension5 = self.env.ref('bs_finance_dimension_spe.bs_dimension_5', raise_if_not_found=False)
        _dimension6 = self.env.ref('bs_finance_dimension_spe.bs_dimension_6', raise_if_not_found=False)
        _dimension7 = self.env.ref('bs_finance_dimension_spe.bs_dimension_7', raise_if_not_found=False)
        _dimension8 = self.env.ref('bs_finance_dimension_spe.bs_dimension_8', raise_if_not_found=False)
        _dimension9 = self.env.ref('bs_finance_dimension_spe.bs_dimension_9', raise_if_not_found=False)
        _dimension10 = self.env.ref('bs_finance_dimension_spe.bs_dimension_10', raise_if_not_found=False)
        
        if res.get('need_finance_dimension_4') and _dimension4:
            res['need_finance_dimension_4']['string'] = f'Need {_dimension4.name}'
        if res.get('need_finance_dimension_5') and _dimension5:
            res['need_finance_dimension_5']['string'] = f'Need {_dimension5.name}'
        if res.get('need_finance_dimension_6') and _dimension6:
            res['need_finance_dimension_6']['string'] = f'Need {_dimension6.name}'
        if res.get('need_finance_dimension_7') and _dimension7:
            res['need_finance_dimension_7']['string'] = f'Need {_dimension7.name}'
        if res.get('need_finance_dimension_8') and _dimension8:
            res['need_finance_dimension_8']['string'] = f'Need {_dimension8.name}'
        if res.get('need_finance_dimension_9') and _dimension9:
            res['need_finance_dimension_9']['string'] = f'Need {_dimension9.name}'
        if res.get('need_finance_dimension_10') and _dimension10:
            res['need_finance_dimension_10']['string'] = f'Need {_dimension10.name}'
        return res