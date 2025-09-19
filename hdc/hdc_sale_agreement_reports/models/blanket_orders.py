# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError,ValidationError

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"
    _description = "Blanket Order"

    @api.model
    def _default_global_discount(self):
        global_discount = self.env['ir.config_parameter'].sudo().get_param(
            'hdc_discount.global_discount_default_product_id')
        return global_discount if global_discount else False

    default_product_global_discount = fields.Many2one('product.product', default = _default_global_discount)

    def check_iso_name(self, check_iso):
        for sale in self:
            check_model = self.env["ir.actions.report"].search([('model', '=', 'quotation.order'),('report_name', '=', check_iso)], limit=1)
            if check_model:
                return check_model.iso_name
            else:
                return "-"
            
    def print(self):
        self.ensure_one()
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.blanket.orders.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.state,
                            "default_sale_blanket_id": self.id
                            },

            }