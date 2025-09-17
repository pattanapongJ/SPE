# Copyright 2023 Basic Solution Co.,Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    vendor_id = fields.Many2one(
        'res.partner',
        string="Vendor",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('supplier_rank', '>', 0)]"
    )
    sale_project_id = fields.Many2one('sale.project', string="Sale Project", tracking=True)


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"
    _description = "Purchase Request"

    pr_reference = fields.Char(string="PR Reference")
    free_text_customer = fields.Char(string="Free Text Customer")

    @api.onchange('team_id')
    def _onchange_team_id(self):
        self.line_ids.update({'team_id': self.team_id.id})
        
class PurchaseRequestsLine(models.Model):
    _inherit = 'purchase.request.line'

    team_id = fields.Many2one("purchase.team", string="Purchase Team")
