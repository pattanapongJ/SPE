# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class DistributionDeliveryNote(models.Model):
    _inherit = "distribition.delivery.note"

    def confirm_action(self):
        for line in self.invoice_line_ids:
            # Update DistributionDeliveryNoteLine
            line.transport_line_id = self.transport_line_id.id
            line.company_round_id = self.company_round_id.id
            line.delivery_status = 'sending'

            # Update invoice
            line.invoice_id.delivery_status = 'sending'
            line.invoice_id.transport_line_id = self.transport_line_id.id
            line.invoice_id.company_round_id = self.company_round_id.id
            line.invoice_id.resend_status = False
            

        self.write({'state': 'in_progress'})

    def closed_action2(self):
        for line in self.invoice_line_ids:
            if line.delivery_status not in ['cancel','resend', 'completed']:
                raise UserError(_("กรุณาระบุ Delivery Status ให้ครบถ้วน ก่อนกดปุ่ม Closed"))

            if line.delivery_status in ['cancel','resend']:
                line.invoice_id.delivery_status = line.delivery_status
                line.invoice_id.billing_status = line.billing_status
                line.invoice_id.finance_type = line.finance_type

            elif line.delivery_status == 'completed':
                if line.billing_status not in ['to_billing', 'to_finance', 'close']:
                    raise UserError(_("กรุณาระบุ Billing Status To Billing / To Finance ก่อนกดปุ่ม Closed"))
                if line.finance_type not in ['cash', 'urgent'] and line.billing_status == 'to_finance':
                    raise UserError(_("กรุณาระบุ สายส่งเงินสด / เงินโอน\n- เงินสด/โอน/เช็ค \n- ด่วนการเงิน \nก่อนกดปุ่ม Closed"))
                line.invoice_id.delivery_status = line.delivery_status
                line.invoice_id.billing_status = line.billing_status
                line.invoice_id.finance_type = line.finance_type
                line.invoice_id.tms_remark = line.tms_remark
                line.invoice_id.cancel_remark = line.cancel_remark
                line.invoice_id.logistics_user_id = self.user_id
                line.invoice_id.delivery_date = self.delivery_date

        self.write({'state': 'close'})
        if self.state == "close":
            order_line = []
            check_back_order = 0
            for invoice_line in self.invoice_line_ids:
                if invoice_line.delivery_status =="resend":
                    transport_line_id = invoice_line.invoice_id.transport_line_id.id
                    check_back_order = 1
                    dict_rec = (0,0,{
                        'invoice_id': invoice_line.invoice_id.id,
                        'partner_id': invoice_line.partner_id.id,
                        'delivery_address_id': invoice_line.delivery_address_id.id,
                        'transport_line_id': invoice_line.transport_line_id.id,
                        'company_round_id': invoice_line.company_round_id.id,
                        'sale_no': invoice_line.sale_no,
                        'delivery_id': invoice_line.delivery_id.id,
                        'sale_person': invoice_line.sale_person.id,
                        'invoice_status': invoice_line.invoice_status,
                        'invoice_date': invoice_line.invoice_id.invoice_date,
                        'remark': invoice_line.remark,
                        'delivery_status':invoice_line.delivery_status,
                        'amount_total':invoice_line.amount_total,
                        'billing_status':invoice_line.billing_status,
                        'finance_type':invoice_line.finance_type})
                    order_line.append(dict_rec)
            if check_back_order == 1:
                context = {}
                context.update({'default_invoice_line_ids' : order_line})
                return {
                        'type': 'ir.actions.act_window',
                        'name': 'Backorder Delivery Order',
                        'res_model': 'wizard.create.back.order',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': context,
                    }
            
    def to_billing_action(self):

        line_ids = []
        for line in self.invoice_line_ids:
            if line.delivery_status == 'completed' and line.billing_status == 'none':
                line_ids.append(line.id)

        return {
            'name': "Billing / Finance", 'view_mode': 'form', 'res_model': 'wizard.billing.finance',
            'type': 'ir.actions.act_window', 'target': 'new', 'context': {
                'default_distribition_id': self.id, 'default_invoice_line_ids': line_ids,
                }
            }

class DistributionDeliveryNoteLine(models.Model):
    _inherit = "distribition.invoice.line"

    billing_status = fields.Selection(
        selection_add=[("close", "Close")],
        ondelete={"distribition.invoice.line": "cascade"})
    
    invoice_cancel_state = fields.Selection([
        ('none', ''),
        ('cancel', 'Cancel'),
    ], string="Invoice Status", default="none")

    finance_type = fields.Selection([
        ('cash', 'เงินสด/โอน/เช็ค'),
        ('urgent', 'ด่วนการเงิน'),
    ], string="สายส่งเงินสด / เงินโอน")  

    @api.onchange('delivery_status')
    def onchange_delivery_status(self):
        if self.delivery_status in ['sending','resend','cancel']:
            self.billing_status = 'none'

    @api.onchange('billing_status')
    def onchange_billing_status(self):
        if self.billing_status in ['to_billing','none']:
            self.finance_type = False
        if self.billing_status == 'close' and self.delivery_status != 'completed':
            raise UserError("You cannot set Billing Status to 'Close' unless Delivery Status is 'Completed'.")
            

    @api.onchange('finance_type')
    def onchange_finance_type(self):
        if self.billing_status != 'to_finance':
            self.finance_type = False

    
