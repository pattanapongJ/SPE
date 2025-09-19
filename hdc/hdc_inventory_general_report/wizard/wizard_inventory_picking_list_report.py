from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardInventoryPickingListReport(models.TransientModel):
    _name = "wizard.inventory.picking.list.report"
    _description = "wizard.inventory.picking.list.report"

    document = fields.Selection([
            ("pk_th_history_portrait", "รายงานใบจัดสินค้า"),
            ("pk_th_history_a5", "รายงานใบจัดสินค้า A5"),
        ],
        string="Document",
        )
    
    state = fields.Char(string='State')
    picking_id = fields.Many2one('stock.picking', string='PK')

    def print(self):
        if self.document == "pk_th_history_portrait":
            return self.env.ref('hdc_inventory_general_report.inventory_picking_list_report_view_th_history_portrait').report_action(self.picking_id)
        if self.document == "pk_th_history_a5":
            return self.env.ref('hdc_inventory_general_report.inventory_picking_list_report_view_th_history_a5').report_action(self.picking_id)
        
