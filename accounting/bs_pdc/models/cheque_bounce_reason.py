# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class ChequeBounceReason(models.Model):
    _name = 'cheque.bounce.reason'
    _description = 'Cheque Bounce Reason'
    _order="code"
    
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !')
    ]

    code = fields.Char('Code', size=64, index=True, copy=False)
    name = fields.Char('Name',copy=False,required=True)
    description = fields.Char('Description')


    
    def name_get(self):
        result = []
        for reason in self:
            name = reason.code + ' ' + reason.name
            result.append((reason.id, name if reason.code else reason.name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            if operator in ('=', '!='):
                domain = ['|', ('code', '=', name.split(' ')[0]), ('name', operator, name)]
            else:
                domain = ['|', ('code', '=ilike', name.split(' ')[0] + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
