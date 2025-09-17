from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardQuotationReport(models.TransientModel):
    _name = "wizard.quotation.report"
    _description = ""

    document = fields.Selection([
        ("th_quotation_discount", "ใบเสนอราคาลูกค้า TH (Quotation) มีแบบส่วนลด"),
        ("th_quotation_no_discount", "ใบเสนอราคาลูกค้า TH (Quotation) ไม่แสดงส่วนลด"),
        ("th_quotation_debt_discount", "ใบเสนอราคา/แจ้งหนี้ แสดงส่วนลด"),
        ("th_quotation_debt_no_discount", "ใบเสนอราคา/แจ้งหนี้ ไม่แสดงส่วนลด"),
        ("en_quotation_discount", "ใบเสนอราคาลูกค้า EN (Quotation) มีแบบส่วนลด"),
        ("en_quotation_no_discount", "ใบเสนอราคาลูกค้า EN (Quotation) ไม่แสดงส่วนลด"),
        ("en_proforma_discount", "ใบแจ้งหนี้ EN (Proforma Invoice) มีแบบส่วนลด"),
        ("en_proforma_no_discount", "ใบแจ้งหนี้ EN (Proforma Invoice) ไม่มีแบบส่วนลด"),
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

    quotation_id = fields.Many2one('quotation.order', string='Quotation')
    state = fields.Char(string='State')


    description_type = fields.Selection([
        ("ex_name_product", "รหัสสินค้า + ชื่อสินค้า"),
        ("name_product", "ชื่อสินค้า"),
        ("pic_name_product", "รูปสินค้า + ชื่อสินค้า"),
        ("barcode_name_product", "บาร์โค้ดสินค้า + ชื่อ"),
        ("ex_barcode_name_product", "รหัสสินค้า + บาร์โค้ดสินค้า + ชื่อสินค้า"),
        ("ex_all_barcode_name_product", "External Item + Barcode Customer + Description Barcode Customer + Description "),
    ],
    string="Form Type",
    default='ex_name_product'
    )

    product_design = fields.Boolean(string="Product Design",default=False)
    
    def print(self):
        # if self.state in ('cancel', 'expired'):
        datas = {
            'type': self.document_type,
            'description_type': self.description_type,
            'quotation_id': self.quotation_id.id,
            'product_design': self.product_design
            }
        # if self.document_type == "normal":
        #     if self.document == "th_quotation_discount":
        #         return self.env.ref('hdc_quotation_order.quotation_th_dis_report_view').report_action(self.quotation_id,data=datas)
        #     if self.document == "th_quotation_no_discount":
        #         return self.env.ref('hdc_quotation_order.quotation_th_no_dis_report_view').report_action(self.quotation_id,data=datas)
        #     if self.document == "en_quotation_discount":
        #         return self.env.ref('hdc_quotation_order.quotation_en_dis_report_view').report_action(self.quotation_id,data=datas)
        #     if self.document == "en_quotation_no_discount":
        #         return self.env.ref('hdc_quotation_order.quotation_en_no_dis_report_view').report_action(self.quotation_id,data=datas)
        #     if self.document == "en_proforma_discount":
        #         return self.env.ref('hdc_quotation_order.proforma_en_dis_report_view').report_action(self.quotation_id,data=datas)
        #     if self.document == "en_proforma_no_discount":
        #         return self.env.ref('hdc_quotation_order.proforma_en_no_dis_report_view').report_action(self.quotation_id,data=datas)
        if self.document_type == "revise":
            if self.document == "th_quotation_discount":
                return self.env.ref('hdc_quotation_order.quotation_th_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "th_quotation_debt_discount":
                return self.env.ref('hdc_quotation_order.quotation_d_th_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "th_quotation_no_discount":
                return self.env.ref('hdc_quotation_order.quotation_th_no_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "th_quotation_debt_no_discount":
                return self.env.ref('hdc_quotation_order.quotation_d_th_no_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "en_quotation_discount":
                return self.env.ref('hdc_quotation_order.quotation_en_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "en_quotation_no_discount":
                return self.env.ref('hdc_quotation_order.quotation_en_no_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "en_proforma_discount":
                return self.env.ref('hdc_quotation_order.proforma_en_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "en_proforma_no_discount":
                return self.env.ref('hdc_quotation_order.proforma_en_no_dis_report_view').report_action(self.quotation_id,data=datas) #
        elif self.document_type == "revise_1":
            if self.document == "th_quotation_discount":
                return self.env.ref('hdc_quotation_order.quotation_th_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "th_quotation_debt_discount":
                return self.env.ref('hdc_quotation_order.quotation_d_th_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "th_quotation_no_discount":
                return self.env.ref('hdc_quotation_order.quotation_th_no_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "th_quotation_debt_no_discount":
                return self.env.ref('hdc_quotation_order.quotation_d_th_no_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "en_quotation_discount":
                return self.env.ref('hdc_quotation_order.quotation_en_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "en_quotation_no_discount":
                return self.env.ref('hdc_quotation_order.quotation_en_no_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "en_proforma_discount":
                return self.env.ref('hdc_quotation_order.proforma_en_dis_report_view').report_action(self.quotation_id,data=datas) #
            if self.document == "en_proforma_no_discount":
                return self.env.ref('hdc_quotation_order.proforma_en_no_dis_report_view').report_action(self.quotation_id,data=datas) #
    
    