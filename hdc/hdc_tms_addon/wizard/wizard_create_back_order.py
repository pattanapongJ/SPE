# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields

class WizardCreateBackOrder(models.TransientModel):
    _name = 'wizard.create.back.order'
    _description = 'Wizard to create back order'

    invoice_line_ids = fields.One2many('wizard.create.back.order.line', 'distribition_line_id', string="Product Lines")

    def create_back_order(self):
        for invoice_line in self.invoice_line_ids:
            invoice_line.delivery_status = False
            invoice_line.invoice_id.finance_type = False
            invoice_line.billing_status = "none"
            invoice_line.invoice_id.billing_status = False
            invoice_line.invoice_id.delivery_status = False
            invoice_line.invoice_id.is_tms = False
            invoice_line.invoice_id.resend_status = "Resend"

class WizardCreateBackOrderLine(models.TransientModel):
    _name = 'wizard.create.back.order.line'
    _description = 'Wizard to create back order line'

    distribition_line_id = fields.Many2one("wizard.create.back.order")
    invoice_id = fields.Many2one('account.move', string="Invoice",
        domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('delivery_status', 'not in', ['sending', 'completed']), ('transport_line_id', '=', transport_line_id)]")
    partner_id = fields.Many2one('res.partner', related='invoice_id.partner_id', string="Customer" )
    transport_line_id = fields.Many2one('delivery.round',string="สายส่ง TRL")
    delivery_status = fields.Selection([
        ('sending', 'Sending'),
        ('resend', 'Resend'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string="Delivery Status")
    submitted_date = fields.Date("Submitted Date")
    remark = fields.Char('Remark')
    delivery_address_id = fields.Many2one("res.partner", string="Delivery Address")
    company_round_id = fields.Many2one(
        "company.delivery.round", string="Mode of delivery"
    )
    sale_no = fields.Char(string="SO No.")
    delivery_id = fields.Many2one("stock.picking", string="Delivery No.")
    sale_person = fields.Many2one("res.users", string="Sale Person")
    invoice_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
    )
    invoice_date = fields.Date("Invoice Date")
    amount_total = fields.Float(string="Price")
    billing_status = fields.Selection(
        [
            ("none", "None"),
            ("to_billing", "To Billing"),
            ("to_finance", "To Finance"),
            ('close', 'Closed'),
        ],
        string="Billing Status",
        default="none",
    )
    finance_type = fields.Selection([
        ('cash', 'เงินสด/โอน/เช็ค'),
        ('urgent', 'ด่วนการเงิน'),
    ], string="สายส่งเงินสด / เงินโอน")  
