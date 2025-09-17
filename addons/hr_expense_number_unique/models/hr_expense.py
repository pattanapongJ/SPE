# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HRExpense(models.Model):
    _inherit = "hr.expense" 


    custom_number = fields.Char(
        string = "Number",
        readonly=True,
        copy=False,
        default=lambda self: _('New')
    )


    @api.model
    def create(self, vals):
        if vals.get('custom_number', _('New')) == _('New'):
            vals['custom_number'] = self.env['ir.sequence'].next_by_code('hr.expense.sequence.custom')
        return super(HRExpense, self).create(vals)