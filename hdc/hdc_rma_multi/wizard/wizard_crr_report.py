from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardCRRReportList(models.TransientModel):
    _name = "wizard.crr.report.list"
    _description = "Wizard CRR Report List"

    document = fields.Selection([
            ("crr_return_customer", "ใบรับสินค้าคืน"),
            ("crr_return_customer_a5", "ใบรับสินค้าคืน A5"),
        ],
        string="Document",
        )
    
    state = fields.Char(string='State')
    picking_id = fields.Many2one('stock.picking', string='Picking')

    def print(self):
        if self.document == "crr_return_customer":
            return self.env.ref('hdc_rma_multi.crr_return_customer_report').report_action(self.picking_id)
        if self.document == "crr_return_customer_a5":
            return self.env.ref('hdc_rma_multi.crr_return_customer_report_a5').report_action(self.picking_id)
        
