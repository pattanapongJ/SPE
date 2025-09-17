# Copyright 2023 Basic Solution Co.,Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    currency_id = fields.Many2one('res.currency',string="Currency", store=True, required=True, domain="[('rate_type', '=', 'sell'), ('active', '=', True)]", default=lambda self: self._default_currency())

    # currency_id = fields.Many2one('res.currency',string="Currency", store=True, required=True, domain="[('rate_type', '=', 'sell'), ('active', '=', True)]")

    @api.model
    def _default_currency(self):
        currency_id = self.env['ir.config_parameter'].sudo().get_param('account_purchase_currency_res_setting')
        return int(currency_id)
    
class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"
    _description = "Purchase Request Line"
    
    purchase_request_line_note = fields.Char(string="Note")