# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    team_id = fields.Many2one('purchase.team', 'Purchase Team', readonly=True)

    def _select(self):
        return super(PurchaseReport, self)._select() + ", po.team_id as team_id"

    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + ", po.team_id"
