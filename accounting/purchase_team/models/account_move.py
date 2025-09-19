# -*- coding: utf-8 -*-
# from pygments.lexer import _inherit

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    purchase_team_id = fields.Many2one(
        'purchase.team', 'Purchase Team', check_company=True,
        store=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

