# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Quotations(models.Model):
    _name = 'quotation.order'
    _inherit = ["quotation.order", "base.revision"]

    current_revision_id = fields.Many2one(
        comodel_name="quotation.order",
    )
    old_revision_ids = fields.One2many(
        comodel_name="quotation.order",
    )
    active = fields.Boolean(default=True,copy=False)

    # Overwrite as sales.order can be multi-company
    _sql_constraints = [
        (
            "revision_unique",
            "unique(unrevisioned_name, revision_number, company_id)",
            "Order Reference and revision must be unique per Company.",
        )
    ]

    def _prepare_revision_data(self, new_revision):
        vals = super()._prepare_revision_data(new_revision)
        vals.update({"state": "cancel"})
        return vals

    def action_view_revisions(self):
        self.ensure_one()
        result = self.env["ir.actions.actions"]._for_xml_id("hdc_quotation_order.action_quotation_orders")
        # result["domain"] = ["|", ("active", "=", False), ("active", "=", True)]
        result["domain"] = [("active", "=", False),("id", "in", self.old_revision_ids.ids)]
        result["context"] = {
            "search_default_current_revision_id": self.id,
            "default_current_revision_id": self.id,
        }
        return result
