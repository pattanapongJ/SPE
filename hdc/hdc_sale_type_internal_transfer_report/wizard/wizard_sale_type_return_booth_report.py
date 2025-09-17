from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardSaleTypeReturnBoothReport(models.TransientModel):
    _name = "wizard.sale.type.return.booth.report"
    _description = "wizard.sale.type.return.booth.report"

    document = fields.Selection([
            ("consignment", "ใบรับคืนสินค้า Consignment"),
        ],
        string="Document",
        )
    
    state = fields.Char(string='State')
    picking_id = fields.Many2one('stock.picking', string='SP')

    def print(self):
        if self.document == "consignment":
            return self.env.ref('hdc_sale_type_internal_transfer_report.sale_type_internal_transfer_report_consignment_return').report_action(self.picking_id)