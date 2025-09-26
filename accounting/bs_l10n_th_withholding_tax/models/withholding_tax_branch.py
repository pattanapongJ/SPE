# -*- coding: utf-8 -*-
from odoo import api, fields, models


class WithholdingTaxCert(models.Model):
    _inherit = "withholding.tax.cert"

    branch_id = fields.Many2one(
        "res.branch",
        string="Branch",
        domain="[('company_id', '=', company_id)]",
        ondelete="restrict",
        tracking=True,
    )

    @api.onchange("company_id")
    def _onchange_company_id_set_branch_domain(self):
        # clear branch when company changes to avoid invalid 
        for rec in self:
            if rec.branch_id and rec.branch_id.company_id != rec.company_id:
                rec.branch_id = False
