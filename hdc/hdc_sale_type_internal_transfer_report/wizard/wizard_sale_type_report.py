from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardSaleTypeBooth(models.TransientModel):
    _name = "wizard.sale.type.report"
    _description = "wizard.sale.type.report"

    document = fields.Selection([
            ("booth", "รายงานใบจัดสินค้า บูธ"),
            ("road_show", "รายงานใบจัดสินค้า Road Show"),
            ("consignment_sale", "รายงานใบจัดสินค้า ฝากขาย"),
            ("consignment", "ใบส่งสินค้าเข้าคลัง Consignment"),
        ],
        string="Document",
        )
    
    state = fields.Char(string='State')
    picking_id = fields.Many2one('stock.picking', string='SP')

    def print(self):
        if self.document == "booth":
            return self.env.ref('hdc_sale_type_internal_transfer_report.sale_type_internal_transfer_report_booth').report_action(self.picking_id)
        if self.document == "road_show":
            return self.env.ref('hdc_sale_type_internal_transfer_report.sale_type_internal_transfer_report_road_show').report_action(self.picking_id)
        if self.document == "consignment_sale":
            return self.env.ref('hdc_sale_type_internal_transfer_report.sale_type_internal_transfer_report_sale_consignment').report_action(self.picking_id)
        if self.document == "consignment":
            return self.env.ref('hdc_sale_type_internal_transfer_report.sale_type_internal_transfer_report_consignment').report_action(self.picking_id)