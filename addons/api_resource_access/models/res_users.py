# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo.osv import expression
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_personalized_access = fields.Boolean()

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        user_ids = []
        if operator not in expression.NEGATIVE_TERM_OPERATORS:
            if operator == 'ilike' and not (name or '').strip():
                domain = [('is_personalized_access','=',False)]
            else:
                domain = [('login', '=', name),('is_personalized_access','=',False)]
            user_ids = self._search(expression.AND([domain, args]), limit=limit,
                                    access_rights_uid=name_get_uid)
        if not user_ids:
            new_domain = [('is_personalized_access','=',False)]
            user_ids = self._search(expression.AND([[('name', operator, name)], args, new_domain]),
                                    limit=limit, access_rights_uid=name_get_uid)
        return user_ids
