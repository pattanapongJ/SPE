# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class PickingList(models.Model):
    _inherit = "picking.lists"


class PickingListLine(models.Model):
    _inherit = "picking.lists.line"

    state_cancel = fields.Boolean(default=False)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("waiting_pick", "Waiting for pickup"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        default="draft",
        store=True,
        compute="_compute_state",
    )

    @api.depends("picking_lists.state", "state_cancel")
    def _compute_state(self):

        for rec in self:
            if rec.state_cancel:
                rec.state = 'cancel'
            else:
                rec.state = rec.picking_lists.state
