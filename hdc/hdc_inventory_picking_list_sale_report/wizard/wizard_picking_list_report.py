from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardPickingListReport(models.TransientModel):
    _name = "wizard.picking.list.report"
    _description = "wizard.picking.list.report"

    document = fields.Selection([
            ("pk_th_history", "รายงานสั่งจัดสินค้า Modern Trade"),
            ("pk_th_history_portrait", "รายงานใบจัดสินค้า"),
            ("pk_th_history_portrait_multi", "รายงานใบจัดสินค้า (Multi Sale Order)"),
            ("pk_th_history_a5", "รายงานใบจัดสินค้า A5"),
            ("pk_th_history_a5_multi", "รายงานใบจัดสินค้า A5 (Multi Sale Order)"),
            ("pk_th_history_1", "รายงานใบจัดสินค้า (รวมยอดจัด)"),

            # ("pk_th_history_portrait_booth", "รายงานใบจัดสินค้าบูท"),
            # ("pk_th_history_portrait_road_show", "รายงานใบจัดสินค้า Road Show"),
            # ("pk_th_history_portrait_consignment_sale", "รายงานใบจัดสินค้าฝากขาย"),
            # ("pk_th_history_portrait_consignment", "รายงานใบจัดสินค้า Consignment"),
        ],
        string="Document",
        )
    
    
    state = fields.Char(string='State')
    picking_id = fields.Many2one('picking.lists', string='PK')

    def print(self):
        if self.document == "pk_th_history":
            return self.env.ref('hdc_inventory_picking_list_sale_report.picking_list_report_view_th_history').report_action(self.picking_id)
        if self.document == "pk_th_history_1":
            return self.env.ref('hdc_inventory_picking_list_sale_report.picking_list_report_view_th_history_1').report_action(self.picking_id)

        if self.document == "pk_th_history_portrait":
            return self.env.ref('hdc_inventory_picking_list_sale_report.picking_list_report_view_th_history_portrait').report_action(self.picking_id)
        if self.document == "pk_th_history_portrait_multi":
            return self.env.ref('hdc_inventory_picking_list_sale_report.picking_list_report_view_th_history_portrait_multi').report_action(self.picking_id)
        if self.document == "pk_th_history_a5":
            return self.env.ref('hdc_inventory_picking_list_sale_report.picking_list_report_view_th_history_a5').report_action(self.picking_id)
        if self.document == "pk_th_history_a5_multi":
            return self.env.ref('hdc_inventory_picking_list_sale_report.picking_list_report_view_th_history_a5_multi').report_action(self.picking_id)

        if self.document == "pk_th_history_portrait_booth":
            return self.env.ref('hdc_inventory_picking_list_sale_report.picking_list_report_view_th_history_portrait_booth').report_action(self.picking_id)
        if self.document == "pk_th_history_portrait_road_show":
            return self.env.ref('hdc_inventory_picking_list_sale_report.picking_list_report_view_th_history_portrait_road_show').report_action(self.picking_id)
        if self.document == "pk_th_history_portrait_consignment_sale":
            return self.env.ref('hdc_inventory_picking_list_sale_report.picking_list_report_view_th_history_portrait_sale_consignment').report_action(self.picking_id)
        if self.document == "pk_th_history_portrait_consignment":
            return self.env.ref('hdc_inventory_picking_list_sale_report.picking_list_report_view_th_history_portrait_consignment').report_action(self.picking_id)