# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

class CrmClaimEpt(models.Model):
    _inherit = "crm.claim.ept"

    crm_claim_ept_line_ids = fields.One2many(comodel_name='crm.claim.ept.line',inverse_name="crm_claim_ept_id" , string='Crm Claim Ept Line IDS')

    claim_amount_total = fields.Float(string="Total Warranty Supplier", readonly=True, store=True)

    tms_remark = fields.Text(string="TMS Remark")

    @api.onchange('crm_claim_ept_line_ids')
    def _onchange_crm_claim_ept_line_ids(self):
        total = 0
        for record in self.crm_claim_ept_line_ids:
            if record.line_subtotal:
                total += record.line_subtotal
        self.claim_amount_total = total
    
    @api.model
    def name_get(self):
        result = []
        for record in self:
            if record.name:
                name = record.name
            else:
                name = record.code
            if record.is_job_no:
                full_name = name + " - [Job no." + record.is_job_no + "]"
                name = full_name
                result.append((record.id,name))
            else:
                full_name = name
                name = full_name
                result.append((record.id,name))
        return result
    
    def print_rma_list(self):
        self.ensure_one()
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.rma.report.list",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.state},
            }
    
class CrmClaimEptLine(models.Model):
    _name = "crm.claim.ept.line"

    crm_claim_ept_id = fields.Many2one(comodel_name='crm.claim.ept', string='Crm Claim Ept ID')

    line_product_id = fields.Many2one('product.product', string='Product', required=True)
    line_description = fields.Char(string='Description')
    line_qty = fields.Float(string='Quantity')
    line_price = fields.Float(string='Price')
    line_subtotal = fields.Float(string='Subtotal', compute="_compute_subtotal", readonly=True, store=True)

    @api.depends('line_qty', 'line_price')
    def _compute_subtotal(self):
        for record in self:
            if record.line_qty > 0 and record.line_price > 0:
                record.line_subtotal = record.line_qty * record.line_price
            else:
                record.line_subtotal = 0

    @api.onchange('line_product_id')
    def _onchange_line_product_id(self):
        for record in self:
            if record.line_product_id:
                record.line_description = record.line_product_id.default_code
