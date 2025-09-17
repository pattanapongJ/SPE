# -*- coding: utf-8 -*-
# Copyright 2023 Basic Solution Co., Ltd. (<https://www.basic-solution.com/>)


from odoo import fields, models


class SaleOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "base.revision"]

    current_revision_id = fields.Many2one(
        comodel_name="purchase.order",
    )
    old_revision_ids = fields.One2many(
        comodel_name="purchase.order",
    )

    # Overwrite as sales.order can be multi-company
    _sql_constraints = [
        (
            "revision_unique",
            "unique(unrevisioned_name, revision_number, company_id)",
            "Order Reference and revision must be unique per Company.",
        )
    ]
