from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardPurchaseReport(models.TransientModel):
    _name = "wizard.purchase.report"
    _description = "wizard.purchase.report"

    document = fields.Selection([
            # ("po", "ใบขอซื้อสินค้า"),
            ("rfq_th", "ใบขอใบเสนอราคา (TH)"),
            ("rfq_en", "ใบขอใบเสนอราคา (EN)"),
            ("po_th", "ใบสั่งซื้อ (TH)"),
            ("po_en", "ใบสั่งซื้อ (EN)"),
            ("po_th_history", "รายงานการสั่งซื้อ"),
            ("po_th_in", "ใบสั่งซื้อ (FM)"),
        ],
        string="Document",
        )
    
    document_purchase = fields.Selection([
        ("po_th", "ใบสั่งซื้อ (TH)"),
        ("po_en", "ใบสั่งซื้อ (EN)"),
        ("po_th_history", "รายงานการสั่งซื้อ"),
        ("po_th_in", "ใบสั่งซื้อ (FM)"),
    ],
    string="Documents"
    )

    state = fields.Char(string='State')
    purchase_id = fields.Many2one('purchase.order', string='PO')

    def print(self):
        if self.document == "rfq_th":
            return self.env.ref('hdc_purchase_general_reports.purchase_order_rfq_report_view_th').report_action(self.purchase_id)
        if self.document == "rfq_en":
            return self.env.ref('hdc_purchase_general_reports.purchase_order_rfq_report_view_en').report_action(self.purchase_id)
        if self.document == "po_th":
            return self.env.ref('hdc_purchase_general_reports.purchase_order_report_view_th').report_action(self.purchase_id)
        if self.document == "po_en":
            return self.env.ref('hdc_purchase_general_reports.purchase_order_report_view_en').report_action(self.purchase_id)
        if self.document == "po_th_history":
            return self.env.ref('hdc_purchase_general_reports.purchase_order_report_view_th_history').report_action(self.purchase_id)
        if self.document == "po_th_in":
            return self.env.ref('hdc_purchase_general_reports.purchase_order_report_view_th_internal').report_action(self.purchase_id)
        if self.document_purchase == "po_th":
            return self.env.ref('hdc_purchase_general_reports.purchase_order_report_view_th').report_action(self.purchase_id)
        if self.document_purchase == "po_en":
            return self.env.ref('hdc_purchase_general_reports.purchase_order_report_view_en').report_action(self.purchase_id)
        if self.document_purchase == "po_th_history":
            return self.env.ref('hdc_purchase_general_reports.purchase_order_report_view_th_history').report_action(self.purchase_id)
        if self.document_purchase == "po_th_in":
            return self.env.ref('hdc_purchase_general_reports.purchase_order_report_view_th_internal').report_action(self.purchase_id)
        
