# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class SaleBorrowPicking(models.Model):
    _inherit = 'stock.picking'
    
    
    

class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "HDC Sale"

    days_delivery = fields.Char(string="Days Delivery")
    
    def print(self):
        self.ensure_one()
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.sale.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.state,
                            "default_sale_id": self.id
                            },

            }
    
    def check_iso_name(self, check_iso):
        for sale in self:
            check_model = self.env["ir.actions.report"].search([('model', '=', 'sale.order'),('report_name', '=', check_iso)], limit=1)
            if check_model:
                return check_model.iso_name
            else:
                return "-"