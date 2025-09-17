from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardBlanketOrderReport(models.TransientModel):
    _name = "wizard.blanket.orders.report"
    _description = "wizard.blanket.orders.report"

    document = fields.Selection([
        ("th_sale_order_discount", "ใบสั่งขายสินค้าลูกค้า TH (Sale Order) มีแบบส่วนลด"),
        ("th_sale_order_no_discount", "ใบสั่งขายสินค้าลูกค้า TH (Sale Order) ไม่มีแบบส่วนลด"),
        ("en_sale_order_discount", "ใบสั่งขายสินค้าลูกค้า EN (Sale Order) มีแบบส่วนลด"),
        ("en_sale_order_no_discount", "ใบสั่งขายสินค้าลูกค้า EN (Sale Order) ไม่มีแบบส่วนลด"),
        ("en_proforma_discount", "ใบแจ้งหนี้ EN (Proforma Invoice) มีแบบส่วนลด"),
        ("en_proforma_no_discount", "ใบแจ้งหนี้ EN (Proforma Invoice) ไม่มีแบบส่วนลด"),
        ("delivery_sale_agreement", "ใบรับฝากสินค้า"),
    ],
    string="Documents"
    )

    document_type = fields.Selection([
        # ("normal", "พิมพ์ปกติ"),
        ("revise", "พิมพ์ปกติ (EX: QT2410-001)"),
        ("revise_1", "เลือกพิมพ์ Revise (EX: QT2410-001-01)"),
    ],
    string="Type",
    default='revise'
    )

    description_type = fields.Selection([
        ("ex_name_product", "รหัสสินค้า + ชื่อสินค้า"),
        ("name_product", "ชื่อสินค้า"),
        ("pic_name_product", "รูปสินค้า + ชื่อสินค้า"),
        ("barcode_name_product", "บาร์โค้ดสินค้า + ชื่อสินค้า"),
        ("ex_barcode_name_product", "รหัสสินค้า + บาร์โค้ดสินค้า + ชื่อสินค้า"),
    ],
    string="Form Type",
    default='ex_name_product'
    )

    sale_blanket_id = fields.Many2one('sale.blanket.order', string='Sale Agreement')
    state = fields.Char(string='State')
    
    def print(self):

        datas = {
            'type': self.document_type,
            'description_type': self.description_type,
            'sale_blanket_id': self.sale_blanket_id.id
        }

        if self.document == "delivery_sale_agreement":
            return self.env.ref('hdc_sale_agreement_reports.account_delivery_sale_agreement').report_action(self.sale_blanket_id) #
                
        if self.document == "th_sale_order_discount":
            return self.env.ref('hdc_sale_agreement_reports.blanket_orders_th_dis_report_view').report_action(self.sale_blanket_id,data=datas) # 
        if self.document == "th_sale_order_no_discount":
            return self.env.ref('hdc_sale_agreement_reports.blanket_orders_th_no_dis_report_view').report_action(self.sale_blanket_id,data=datas) #
        if self.document == "en_sale_order_discount":
            return self.env.ref('hdc_sale_agreement_reports.blanket_orders_en_dis_report_view').report_action(self.sale_blanket_id,data=datas) #
        if self.document == "en_sale_order_no_discount":
            return self.env.ref('hdc_sale_agreement_reports.blanket_orders_en_no_dis_report_view').report_action(self.sale_blanket_id,data=datas) #
        if self.document == "en_proforma_discount":
            return self.env.ref('hdc_sale_agreement_reports.blanket_orders_proforma_en_dis_report_view').report_action(self.sale_blanket_id,data=datas) #
        if self.document == "en_proforma_no_discount":
            return self.env.ref('hdc_sale_agreement_reports.blanket_orders_proforma_en_no_dis_report_view').report_action(self.sale_blanket_id,data=datas) #
   