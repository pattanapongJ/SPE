# -*- coding: utf-8 -*-
from odoo import api,models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange("team_id")
    def _onchange_team_id_sale_team_addon(self):
        domain_sale_spec = [('id', 'in', self.team_id.sale_spec_member_ids.ids)]
        return {'domain': {'sale_spec':domain_sale_spec}}