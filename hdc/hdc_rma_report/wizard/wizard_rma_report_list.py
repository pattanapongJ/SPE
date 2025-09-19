from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardRMAReportList(models.TransientModel):
    _name = "wizard.rma.report.list"
    _description = "Wizard RMA Report List"

    document = fields.Selection([
            ("rma_product_change", "รายงานใบเปลี่ยนสินค้า"),
            ("rma_product_refun", "ใบรับเรื่องคืนสินค้าลูกค้า"),
            ("picking_list", "รายงานใบจัดสินค้า A5"),
        ],
        string="Document",
        )
    
    state = fields.Char(string='State')
    rma_id = fields.Many2one('crm.claim.ept', string='RMA')

    def print(self):
        if self.document == "rma_product_change":
            return self.env.ref('hdc_rma_report.rma_product_change_report_view').report_action(self.rma_id)
        elif self.document == "rma_product_refun":
            return self.env.ref('rma_ept.action_report_rma').report_action(self.rma_id)
        elif self.document == "picking_list":
            return self.env.ref('hdc_rma_dewalt.picking_list_report_dewalt_a5').report_action(self.rma_id)
        
