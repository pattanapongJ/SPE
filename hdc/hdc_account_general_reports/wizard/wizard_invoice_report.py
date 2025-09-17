from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardInvoiceReport(models.TransientModel):
    _name = "wizard.invoice.report"
    _description = "wizard.invoice.report"

    document = fields.Selection([
            ("inv", "ใบแจ้งหนี้"),
            ("bill", "ใบวางบิล-ใบเสร็จ-ใบกำกับ"),
            ("receipt", "ใบเสร็จรับเงิน"),
            ("tax", "ใบกำกับภาษี"),
            ("credit", "ใบลดหนี้/ใบกำกับภาษี"), ("debit", "ใบเพิ่มหนี้/ใบกำกับภาษี"),
            # ("borrow_new_invoice", "ใบส่งสินค้าตัวอย่าง"),
            ("borrow_free_invoice", "ใบส่งสินค้าตัวอย่าง (ฟรี)"),
            ("borrow_return_invoice", "ใบส่งสินค้าตัวอย่าง (รับกลับคืน)"),
            ("borrow_test_money_invoice", "ใบส่งสินค้าตัวอย่าง (ทดสอบผ่านคิดเงิน)"),
            ("temp_delivery", "ใบส่งสินค้าชั่วคราว"),
            ("temp_delivery_price", "ใบส่งสินค้าชั่วคราวแบบมีราคา"),
            ("delivery", "ใบส่งของ"),
            ("delivery_price", "ใบส่งของมีราคา"),
        ],
        string="ชือเอกสาร",
        required=True)
    type = fields.Selection([
            ("original", "ต้นฉบับ"),
            ("copy", "สำเนา"),
            ("duo", "ต้นฉบับ และสำเนา"),
        ],
        string="ประเภทการพิมพ์",
        required=True, default="original")

    account_id = fields.Many2one('account.move', string='account')

    def print(self):

        if self.document == "delivery":
            return self.env.ref('hdc_account_general_reports.account_invoices_delivery').report_action(self.account_id)
        if self.document == "delivery_price":
            return self.env.ref('hdc_account_general_reports.account_invoices_delivery_price').report_action(self.account_id)
        if self.document == "temp_delivery_price":
            return self.env.ref('hdc_account_general_reports.account_invoices_temp_delivery_price').report_action(self.account_id)
        if self.document == "temp_delivery":
            return self.env.ref('hdc_account_general_reports.account_invoices_temp_delivery').report_action(self.account_id)
        # if self.document == "borrow_new_invoice":
        #     return self.env.ref('hdc_account_general_reports.invoice_borrow_new_report_view').report_action(self.account_id)
        if self.document == "borrow_free_invoice":
            return self.env.ref('hdc_account_general_reports.invoice_borrow_free_report_view').report_action(self.account_id)
        if self.document == "borrow_return_invoice":
            return self.env.ref('hdc_account_general_reports.invoice_borrow_return_report_view').report_action(self.account_id)
        if self.document == "borrow_test_money_invoice":
            return self.env.ref('hdc_account_general_reports.invoice_borrow_test_money_report_view').report_action(self.account_id)

        elif self.type == "original":
            if self.document == "inv":
                return self.env.ref('account.account_invoices').report_action(self.account_id)
            elif self.document == "bill":
                return self.env.ref('hdc_account_general_reports.account_invoices_bill').report_action(self.account_id)
            elif self.document == "receipt":
                return self.env.ref('hdc_account_general_reports.account_invoices_receipt').report_action(self.account_id)
            elif self.document == "tax":
                return self.env.ref('hdc_account_general_reports.account_invoices_tax').report_action(self.account_id)
            elif self.document == "credit":
                return self.env.ref('hdc_account_general_reports.account_invoices_credit').report_action(self.account_id)
            elif self.document == "debit":
                return self.env.ref('hdc_account_general_reports.account_invoices_debit').report_action(self.account_id)

        elif self.type == "copy":
            if self.document == "inv":
                return self.env.ref('hdc_account_general_reports.account_invoices_copy').report_action(self.account_id)
            elif self.document == "bill":
                return self.env.ref('hdc_account_general_reports.account_invoices_bill_copy').report_action(self.account_id)
            elif self.document == "receipt":
                return self.env.ref('hdc_account_general_reports.account_invoices_receipt_copy').report_action(self.account_id)
            elif self.document == "tax":
                return self.env.ref('hdc_account_general_reports.account_invoices_tax_copy').report_action(self.account_id)
            elif self.document == "credit":
                return self.env.ref('hdc_account_general_reports.account_invoices_credit_copy').report_action(self.account_id)
            elif self.document == "debit":
                return self.env.ref('hdc_account_general_reports.account_invoices_debit_copy').report_action(self.account_id)
        else:
            if self.document == "inv":
                return self.env.ref('hdc_account_general_reports.account_invoices_all').report_action(self.account_id)
            elif self.document == "bill":
                return self.env.ref('hdc_account_general_reports.account_invoices_bill_all').report_action(self.account_id)
            elif self.document == "receipt":
                return self.env.ref('hdc_account_general_reports.account_invoices_receipt_all').report_action(self.account_id)
            elif self.document == "tax":
                return self.env.ref('hdc_account_general_reports.account_invoices_tax_all').report_action(self.account_id)
            elif self.document == "credit":
                return self.env.ref('hdc_account_general_reports.account_invoices_credit_all').report_action(self.account_id)
            elif self.document == "debit":
                return self.env.ref('hdc_account_general_reports.account_invoices_debit_all').report_action(self.account_id)

