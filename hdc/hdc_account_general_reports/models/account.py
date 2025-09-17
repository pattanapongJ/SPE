from odoo import fields, models, api, _
import qrcode
import base64
from io import StringIO, BytesIO, TextIOWrapper
import json

class AccountMove(models.Model):
    _inherit = "account.move"

    contact_person = fields.Many2one(
        'res.partner', string='Contact Person', readonly=False)
    
    @api.model
    def _default_global_discount(self):
        global_discount = self.env['ir.config_parameter'].sudo().get_param(
            'hdc_discount.global_discount_default_product_id')
        return global_discount if global_discount else False
    
    default_product_global_discount = fields.Many2one('product.product', default = _default_global_discount)

    def check_product_global_discount(self,product_id):
        if product_id.id == self.default_product_global_discount.id:
            return "Yes"
        else:
            return "No"
        
    @api.onchange('partner_id')
    def _domain_contact_person(self):
        if self.partner_id:
            self.contact_person = False
            return {"domain": {
                "contact_person": [('type', '=', "contact"),
                                   ('id', '=', self.partner_id.child_ids.ids)],
            }}
        else:
            self.contact_person = False
            return {
                "domain": {
                    "contact_person": [('type', '=', "contact")],
                }
            }

    def generate_qr_code(self, invoice):
        # Create the QR code image
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10,
                           border=4,)
        qr.add_data(invoice)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Encode the image as a base64 string
        with BytesIO() as buffer:
            img.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
    

    def get_widget_amount_info(self):
        sum_amount = 0.0
        try:
            data_dict = json.loads(self.invoice_payments_widget)
        except Exception as e:
            return sum_amount

        content_list = data_dict.get("content", [])
        for line in content_list:
            amt = line.get("amount", 0.0)
            sum_amount += amt

        return sum_amount

    def check_stamp_report(self, check_stamp_report):
        for billing in self:
            check_model = self.env["ir.actions.report"].search([('model', '=', 'account.move'),('report_name', '=', check_stamp_report)], limit=1)
            if check_model:
                return check_model.stamp_report
            else:
                return "-"

        
    def get_account_payment_id_before_name(self):
        payment_id_name = ""
        invoice_payments_widget_data = self.invoice_payments_widget.split(',')
        payment_ids = []
        for item in invoice_payments_widget_data:
            if "account_payment_id" in item:
                account_payment_id_data = item.split(' ')
                try:
                    payment_ids.append(int(account_payment_id_data[2]))
                except ValueError:
                    # ถ้าไม่สามารถแปลงเป็น int ได้ ให้ข้ามค่าดังกล่าว
                    continue
        if len(payment_ids) > 1:
            account_payment_id = self.env['account.payment'].search([('id','=',payment_ids[-2])], limit=1)
            payment_id_name = account_payment_id.name
        return payment_id_name

    

#     def print_account_invoices_copy(self):
#         return self.env.ref('hdc_account_general_reports.account_invoices_copy').report_action(self)
#


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # def print_account_tax_invoices(self):
    #     return self.env.ref('hdc_account_general_reports.account_tax_invoices').report_action(self)

    # def print_account_tax_invoices_copy(self):
    #     return self.env.ref('hdc_account_general_reports.account_tax_invoices_copy').report_action(self)

    def print_account_payment_voucher(self):
        if self.payment_type == "outbound":
            return self.env.ref('hdc_account_general_reports.account_payment_voucher').report_action(self)
        else:
            return self.env.ref('hdc_account_general_reports.account_receipt_voucher').report_action(self)

    # def print_account_payment_receipt(self):
    #     return self.env.ref('account.action_report_payment_receipt').report_action(self)

    def get_currency_rate(self):
        currency_rate = 0
        if self.move_id:
            if self.move_id.date and self.currency_id:
                currency_rate_ids = self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id)],order="name desc")
                for item in currency_rate_ids:
                    if item.name <= self.move_id.date:
                        currency_rate = item.inverse_company_rate
                        return currency_rate
        return currency_rate

# class AccountBill(models.Model):
#     _inherit = "account.billing"

