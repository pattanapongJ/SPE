from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardSaleReport(models.TransientModel):
    _name = "wizard.sale.report"
    _description = "wizard.sale.report"

    document = fields.Selection([
        ("th_quotation_discount", "ใบเสนอราคาลูกค้า TH (Quotation) มีแบบส่วนลด"),
        ("th_quotation_no_discount", "ใบเสนอราคาลูกค้า TH (Quotation) ไม่แสดงส่วนลด"),
        ("th_quotation_d_discount", "ใบเสนอราคา/แจ้งหนี้ แสดงส่วนลด"),
        ("th_quotation_d_no_discount", "ใบเสนอราคา/แจ้งหนี้ ไม่แสดงส่วนลด"),
        ("en_quotation_discount", "ใบเสนอราคาลูกค้า EN (Quotation) มีแบบส่วนลด"),
        ("en_quotation_no_discount", "ใบเสนอราคาลูกค้า EN (Quotation) ไม่แสดงส่วนลด"),
        ("en_proforma_discount", "ใบแจ้งหนี้ EN (Proforma Invoice) มีแบบส่วนลด"),
        ("en_proforma_no_discount", "ใบแจ้งหนี้ EN (Proforma Invoice) ไม่มีแบบส่วนลด"),
        ("delivery_booth_qo", "ใบส่งสินค้าออกบูธ TH"),
        ("delivery_booth_en", "ใบส่งสินค้าออกบูธ EN"),
    ],
    string="Documents"
    )
    
    document_sale = fields.Selection([
        ("th_sale_order_discount", "ใบสั่งขายสินค้าลูกค้า TH (Sale Order) มีแบบส่วนลด"),
        ("th_sale_order_no_discount", "ใบสั่งขายสินค้าลูกค้า TH (Sale Order) ไม่มีแบบส่วนลด"),
        ("th_sale_d_order_discount", "ใบเสนอราคา/แจ้งหนี้ แสดงส่วนลด"),
        ("th_sale_d_order_no_discount", "ใบเสนอราคา/แจ้งหนี้ ไม่แสดงส่วนลด"),
        ("en_sale_order_discount", "ใบสั่งขายสินค้าลูกค้า EN (Sale Order) มีแบบส่วนลด"),
        ("en_sale_order_no_discount", "ใบสั่งขายสินค้าลูกค้า EN (Sale Order) ไม่มีแบบส่วนลด"),
        ("en_proforma_discount", "ใบแจ้งหนี้ EN (Proforma Invoice) มีแบบส่วนลด"),
        ("en_proforma_no_discount", "ใบแจ้งหนี้ EN (Proforma Invoice) ไม่มีแบบส่วนลด"),
        ("delivery_booth_so", "ใบส่งสินค้าออกบูธ TH"),
        ("delivery_booth_en", "ใบส่งสินค้าออกบูธ EN"),
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
        ("barcode_name_product", "บาร์โค้ดสินค้า + ชื่อ"),
        ("ex_barcode_name_product", "รหัสสินค้า + บาร์โค้ดสินค้า + ชื่อสินค้า"),
        ("ex_barcode_cus_product", "External Item + Barcode Customer + Description"),
    ],
    string="Barcode",
    default='ex_name_product'
    )

    sale_id = fields.Many2one('sale.order', string='SO')
    state = fields.Char(string='State')
    
    def print(self):

        datas = {
        'type': self.document_type,
        'description_type': self.description_type,
        'sale_id': self.sale_id.id
        }
                
        if self.document == "th_quotation_discount":
            return self.env.ref('hdc_sale_general_reports.quotation_th_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document == "th_quotation_d_discount":
            return self.env.ref('hdc_sale_general_reports.quotation_d_th_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document == "th_quotation_no_discount":
            return self.env.ref('hdc_sale_general_reports.quotation_th_no_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document == "th_quotation_d_no_discount":
            return self.env.ref('hdc_sale_general_reports.quotation_d_th_no_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document == "en_quotation_discount":
            return self.env.ref('hdc_sale_general_reports.quotation_en_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document == "en_quotation_no_discount":
            return self.env.ref('hdc_sale_general_reports.quotation_en_no_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document == "en_proforma_discount":
            return self.env.ref('hdc_sale_general_reports.proforma_en_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document == "en_proforma_no_discount":
            return self.env.ref('hdc_sale_general_reports.proforma_en_no_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document == "delivery_booth_qo":
            return self.env.ref('hdc_sale_general_reports.delivery_booth_qo_report_view').report_action(self.sale_id,data=datas) #
        elif self.document == "delivery_booth_en":
            return self.env.ref('hdc_sale_general_reports.delivery_booth_en_report_view').report_action(self.sale_id,data=datas) #
        
        elif self.document_sale == "th_sale_order_discount":
            return self.env.ref('hdc_sale_general_reports.sale_order_th_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document_sale == "th_sale_d_order_discount":
            return self.env.ref('hdc_sale_general_reports.sale_d_order_th_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document_sale == "th_sale_order_no_discount":
            return self.env.ref('hdc_sale_general_reports.sale_order_th_no_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document_sale == "th_sale_d_order_no_discount":
            return self.env.ref('hdc_sale_general_reports.sale_d_order_th_no_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document_sale == "en_sale_order_discount":
            return self.env.ref('hdc_sale_general_reports.sale_order_en_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document_sale == "en_sale_order_no_discount":
            return self.env.ref('hdc_sale_general_reports.sale_order_en_no_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document_sale == "en_proforma_discount":
            return self.env.ref('hdc_sale_general_reports.proforma_en_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document_sale == "en_proforma_no_discount":
            return self.env.ref('hdc_sale_general_reports.proforma_en_no_dis_report_view').report_action(self.sale_id,data=datas) #
        elif self.document_sale == "delivery_booth_so":
            return self.env.ref('hdc_sale_general_reports.delivery_booth_so_report_view').report_action(self.sale_id,data=datas) #
        elif self.document_sale == "delivery_booth_en":
            return self.env.ref('hdc_sale_general_reports.delivery_booth_en_report_view').report_action(self.sale_id,data=datas) #
        