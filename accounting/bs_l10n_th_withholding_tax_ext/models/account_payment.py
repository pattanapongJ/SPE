# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    
    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        line_vals_list = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
        if write_off_line_vals:
            for vals in line_vals_list:
                if isinstance(write_off_line_vals, list):
                    for wline in write_off_line_vals:
                        if 'wt_tax_id' not in wline or vals.get('name') != wline.get('name') or vals.get(
                                'account_id') != wline.get(
                            'account_id'):
                            continue
                        vals['wt_tax_id'] = wline.get('wt_tax_id')
        return line_vals_list
