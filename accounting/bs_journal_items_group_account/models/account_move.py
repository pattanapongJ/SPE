# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    
    move_line_group_ids = fields.One2many(
        string=_('Move_line_group_ids'),
        comodel_name='account.move.line.group',
        inverse_name='move_id',
        compute='_compute_move_line_group_ids'
    )
    
    def check_group_mode(self):
        is_group = self.env['ir.config_parameter'].sudo().get_param("is_group_account", default=False)
        return is_group
    
    @api.depends('line_ids','line_ids.name','line_ids.account_id','line_ids.debit','line_ids.credit')
    def _compute_move_line_group_ids(self):
        for move in self:
            if self.check_group_mode():
                domain = [
                    ('move_id', '=', move.id),
                    ('group_mode', '=', 'group')
                ]
            else:
                domain = [
                    ('move_id', '=', move.id),
                    ('group_mode', '=', 'split')
                ]
            moves = self.env['account.move.line.group'].search(domain)
            move.move_line_group_ids = moves