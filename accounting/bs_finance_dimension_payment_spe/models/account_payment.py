# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _get_finance_dimension_values(self, source):
        vals = super(AccountPayment, self)._get_finance_dimension_values(source)
        vals.update({
            'finance_dimension_4_id': source.get('finance_dimension_4_id'),
            'finance_dimension_5_id': source.get('finance_dimension_5_id'),
            'finance_dimension_6_id': source.get('finance_dimension_6_id'),
            'finance_dimension_7_id': source.get('finance_dimension_7_id'),
            'finance_dimension_8_id': source.get('finance_dimension_8_id'),
            'finance_dimension_9_id': source.get('finance_dimension_9_id'),
            'finance_dimension_10_id': source.get('finance_dimension_10_id')
        })

        return vals
