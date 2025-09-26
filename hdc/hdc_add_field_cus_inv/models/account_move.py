# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

class AccountMove(models.Model):
    _inherit = 'account.move'

    # due_payment = fields.Date(string="Due Payment", default=lambda self: self._get_default_date_due_payment_term())
    # due_payment = fields.Date(string="Due Payment")


    due_payment = fields.Date(string="Due Payment", compute="_compute_add_field_cus_inv", store=True)

    cn_reference = fields.Char(string="CN Reference", compute="_compute_add_field_cus_inv")
    dn_reference = fields.Char(string="DN Reference", compute="_compute_add_field_cus_inv")
    customer_account = fields.Many2one('res.partner', string="Customer Account", compute="_compute_add_field_cus_inv")
    customer_code = fields.Char(string="Customer Code", compute="_compute_add_field_cus_inv")
    financial_note = fields.Char(string="Financial Note")
    accounting_note = fields.Char(string="Accounting Note")
    pdc_date = fields.Date(string="PDC Date", compute="_compute_add_field_cus_inv")
    pdc_no = fields.Char(string="PDC No", compute="_compute_add_field_cus_inv")
    pdc_status = fields.Selection(string="PDC Status", selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], compute="_compute_add_field_cus_inv")
    commission_date = fields.Date(string="Commission Date", compute="_compute_add_field_cus_inv")
    number_paid_at = fields.Char(string="เลขที่ใบถูกหัก ณ ที่จ่าย")
    payment_date = fields.Date(string="Payment Date", compute="_compute_add_field_cus_inv")
    payment_no = fields.Char(string="Payment No.", compute="_compute_add_field_cus_inv")
    billing_date = fields.Date(string="Billing Date", compute="_compute_add_field_cus_inv")
    billing_no = fields.Char(string="Billing No.", compute="_compute_add_field_cus_inv")
    batch_billing_no = fields.Char(string="Batch Billing No.", compute="_compute_add_field_cus_inv")
    delivery_tracking = fields.Char(string="Delivery Tracking")
    commission_note = fields.Char(string="Commission Notes")
    billing_note = fields.Char(string="Billing Notes")
    billing_receipt_date = fields.Date(string="Billing Receipt Dates")
    # @api.onchange('invoice_date_due_payment_term')
    # def _onchange_invoice_date_due(self):
    #     for record in self:
    #         if record.invoice_date_due_payment_term:
    #             record.due_payment = record.invoice_date_due_payment_term

    # @api.depends('invoice_date_due')
    def _compute_add_field_cus_inv(self):
        # อย่าลืมมาทำ fields store=True ด้วยนะ

        for record in self:
            # Find CN Reference Value
            if record.refund_invoice_ids:
                if record.refund_invoice_ids[0].name:
                    record.cn_reference = record.refund_invoice_ids[0].name
                else:
                    record.cn_reference = None
            else:
                record.cn_reference = None            

            # Find DN Reference Value
            if record.debit_note_ids:
                if record.debit_note_ids[0].name:
                    record.dn_reference = record.debit_note_ids[0].name
                else:
                    record.dn_reference = None
            else:
                record.dn_reference = None            

            # Find Customer Account Value From Sale Order
            find_so = self.env['sale.order'].search([('invoice_ids', 'in', [record.id])])
            if find_so:
                record.customer_account = find_so[0].partner_id
                record.customer_code = find_so[0].partner_id.ref
            else:
                record.customer_account = None
                record.customer_code = None                      

            invoice_payments_widget_data = record.invoice_payments_widget.split(',')
            payment_ids = []       

            for item in invoice_payments_widget_data:
                if "account_payment_id" in item:
                    account_payment_id_data = item.split(' ')

                    try:
                        payment_ids.append(int(account_payment_id_data[2]))
                    except:
                        pass                   

            if len(payment_ids) > 0:
                account_payment_id = self.env['account.payment'].search([('id','=',payment_ids[0])])
                if account_payment_id:
                    record.commission_date = account_payment_id.commission_date
                    record.payment_date = account_payment_id.date
                    record.payment_no = account_payment_id.name
                    record.pdc_status = account_payment_id.state
                    if account_payment_id.pdc_id:
                        record.pdc_date = account_payment_id.pdc_id.payment_date
                        record.pdc_no = account_payment_id.pdc_id.name
                        # if account_payment_id.pdc_id.state in ['draft', 'posted', 'cancel']:
                        #     record.pdc_status = account_payment_id.pdc_id.state
                        # else:
                        #     record.pdc_status = None
                    else:
                        record.pdc_date = None
                        record.pdc_no = None
                        # record.pdc_status = None
                else:
                    record.commission_date = None
                    record.payment_date = None
                    record.payment_no = None
                    record.pdc_date = None
                    record.pdc_no = None
                    record.pdc_status = None
            else:
                record.commission_date = None
                record.payment_date = None
                record.payment_no = None
                record.pdc_date = None
                record.pdc_no = None
                record.pdc_status = None
            
            if record.billing_ids:
                first = 0
                for bill_id in record.billing_ids:
                    if first == 0:
                        record.billing_date = bill_id.date
                        record.billing_no = bill_id.name
                        record.batch_billing_no = bill_id.batch_billing_no
                        first += 1
            else:
                record.billing_date = None
                record.billing_no = None
                record.batch_billing_no = None

            if record.due_payment is None:
                # print('----------> record.due_payment None', record.invoice_date_due)
                if record.invoice_date_due:
                    # print('----------> record.invoice_date_due', record.invoice_date_due)
                    record.due_payment = record.invoice_date_due
            elif record.due_payment is False:
                # print('----------> record.due_payment False', record.invoice_date_due)
                if record.invoice_date_due:
                    # print('----------> record.invoice_date_due', record.invoice_date_due)
                    record.due_payment = record.invoice_date_due
            elif record.due_payment:
                # print('----------> record.due_payment', record.invoice_date_due)
                record.due_payment = record.due_payment
            else:
                record.due_payment = None

    #     for record in self:
    #         print('--------->_compute_invoice_date_due', record.invoice_date_due)
    #         due_payment_term = record.invoice_date_due
    #         if due_payment_term:
    #             print('--------->due_payment_term', due_payment_term)
    #             record.due_payment = due_payment_term

    # @api.model
    # def _get_default_date_due_payment_term(self):
    #     due_payment_term = self.invoice_date_due_payment_term
    #     print('-------> due_payment_term', due_payment_term)
    #     if due_payment_term:
    #         return due_payment_term
    #     return None
