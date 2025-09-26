# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DistributionDeliveryNote(models.Model):
    _name = "distribition.delivery.note"
    _description = "Distribution Delivery Note"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string = "Distribution Delivery Note", required = True, readonly = True, translate = True,
                       default = 'New')

    transport_line = fields.Char(string = "Transport Line")
    transport_line_id = fields.Many2one('delivery.round', string = "สายส่ง TRL")
    company_round_id = fields.Many2one('company.delivery.round', string = "Mode of delivery")
    transport_desc = fields.Char(related = 'transport_line_id.code', string = "สายส่ง TRL Description")
    company_round_desc = fields.Char(related = 'company_round_id.code', string = "Mode of delivery Description")
    total_weight = fields.Float(string = "Total Weight", digits = (16, 2))
    # scheduled_date = fields.Datetime("Scheduled Date", default=lambda self: fields.Date.today())
    schedule_date = fields.Date(string = "Scheduled Date", default = lambda self: fields.Date.today())
    delivery_date = fields.Date(string = "Delivery Date", readonly = True)
    delivery_by_id = fields.Char(string = "Delivery By", )
    car_code = fields.Char(string = "ทะเบียนรถ", )
    car_type = fields.Char(string = "ประเภทรถ", )
    driver_name = fields.Char(string = "คนขับรถ", )
    driver_assistant_name = fields.Char(string = "ผู้ช่วยคนขับรถ", )
    state = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In Progress'), ('delivery', 'Delivery'), ('close', 'Closed'),
         ('cancel', 'Cancelled'), ], string = 'Status', readonly = True, default = 'draft', tracking = True, )

    user_id = fields.Many2one('res.users', string = "Logistics Operator", default = lambda self: self.env.user)
    distribition_line_ids = fields.One2many('distribition.delivery.note.line', 'distribition_line_id',
                                            string = "Product Lines")
    invoice_line_ids = fields.One2many('distribition.invoice.line', 'distribition_id', string = "Invoice Lines")
    invoice_finance_count = fields.Integer(compute = "_compute_invoice_count")
    invoice_billing_count = fields.Integer(compute = "_compute_invoice_count")
    driver_id = fields.Many2one('driver.model', string = "Driver")
    car_registration = fields.Char('ทะเบียนรถ', related = 'driver_id.car_registration', readonly = False)
    company_id = fields.Many2one("res.company", string = "Company",)
    tms_remark = fields.Char('TMS Remark')
    cancel_remark = fields.Char('Cancel Remark')

    billing_status_remark = fields.Selection([('none', 'None'), 
                                              ('to_billing', 'To Billing'), 
                                              ('to_finance', 'To Finance'),
                                              ("close", "Close")],
                                      string = "Billing Status", default = 'none')

    cancel_status_remark = fields.Selection([('none', 'None'), 
                                              ("close", "Close")],
                                      string = "Billing Status", default = 'none')

    def _compute_invoice_count(self):
        for res in self:
            invoice_finance_count = 0
            invoice_billing_count = 0

            for line in res.invoice_line_ids:
                if line.invoice_id.billing_status in ['to_billing', 'billing']:
                    invoice_billing_count += 1
                if line.invoice_id.billing_status in ['to_finance', 'finance']:
                    invoice_finance_count += 1

            res.invoice_finance_count = invoice_finance_count
            res.invoice_billing_count = invoice_billing_count

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
            # line.invoice_id.tms_remark = line.tms_remark

        self.write({'state': 'in_progress'})

    def delivery_action(self):
        for line in self.invoice_line_ids:
            # Update DistributionDeliveryNoteLine
            line.delivery_status = 'completed'

            # Update invoice
            line.invoice_id.delivery_status = 'completed'
            line.invoice_id.tms_remark = line.tms_remark

        self.write({'state': 'delivery', 'delivery_date': fields.Date.today()})

    def closed_action(self):
        for line in self.invoice_line_ids:
            if line.delivery_status not in ['resend', 'completed']:
                raise UserError(_("กรุณาระบุ Delivery Status ให้ครบถ้วน ก่อนกดปุ่ม Closed"))

            if line.delivery_status == 'resend':
                line.invoice_id.delivery_status = line.delivery_status
                line.invoice_id.billing_status = line.billing_status

            elif line.delivery_status == 'completed':
                if line.billing_status not in ['to_billing', 'to_finance']:
                    raise UserError(_("กรุณาระบุ Billing Status To Billing / To Finance ก่อนกดปุ่ม Closed"))

                line.invoice_id.delivery_status = line.delivery_status
                line.invoice_id.billing_status = line.billing_status

        self.write({'state': 'close'})

    def to_billing_action(self):

        line_ids = []
        for line in self.invoice_line_ids:
            if line.delivery_status == 'completed':
                line_ids.append(line.id)

        return {
            'name': "Billing / Finance", 'view_mode': 'form', 'res_model': 'wizard.billing.finance',
            'type': 'ir.actions.act_window', 'target': 'new', 'context': {
                'default_distribition_id': self.id, 'default_invoice_line_ids': line_ids,
                }
            }

    def cancel_action(self):
        for line in self.invoice_line_ids:
            # Update DistributionDeliveryNoteLine
            line.delivery_status = 'cancel'

            # Update invoice
            line.invoice_id.delivery_status = 'cancel'
            line.invoice_id.is_tms = False
            sale_id = self.env['sale.order'].search([('name', '=', line.sale_no)])
            sale_id.is_tms = False

        self.write({'state': 'cancel'})

    def unlink(self):
        for line in self.invoice_line_ids:
            line.delivery_status = 'cancel'
            line.invoice_id.delivery_status = 'cancel'
            line.invoice_id.is_tms = False
            sale_id = self.env['sale.order'].search([('name', '=', line.sale_no)])
            sale_id.is_tms = False
        return super(DistributionDeliveryNote, self).unlink()

    def action_view_invoice_finance(self):
        # choose the view_mode accordingly
        invoice_ids = []
        for line in self.invoice_line_ids:
            if line.invoice_id.billing_status in ['to_finance', 'finance']:
                invoice_ids.append(line.invoice_id.id)

        action = {
            'name': _('Invoices Finance'), 'type': 'ir.actions.act_window', 'res_model': 'account.move',
            'target': 'current',
            }

        if len(invoice_ids) == 1:
            invoice = invoice_ids[0]
            action['res_id'] = invoice
            action['view_mode'] = 'form'
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', invoice_ids)]
        return action

    def action_view_invoice_billing(self):
        # choose the view_mode accordingly
        invoice_ids = []
        for line in self.invoice_line_ids:
            if line.invoice_id.billing_status in ['to_billing', 'billing']:
                invoice_ids.append(line.invoice_id.id)

        action = {
            'name': _('Invoices Billing'), 'type': 'ir.actions.act_window', 'res_model': 'account.move',
            'target': 'current',
            }

        if len(invoice_ids) == 1:
            invoice = invoice_ids[0]
            action['res_id'] = invoice
            action['view_mode'] = 'form'
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', invoice_ids)]
        return action

    @api.depends("invoice_line_ids")
    def _compute_max_line_sequence(self):
        for sale in self:
            sale.max_line_sequence = max(sale.mapped("invoice_line_ids.sequence") or [0]) + 1

    max_line_sequence = fields.Integer(
        string="Max sequence in lines", compute="_compute_max_line_sequence", store=True
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('distribition_delivery_note_sequence') or _('New')
        line = super(DistributionDeliveryNote, self).create(vals)
        line._reset_sequence()
        return line
    
    def write(self, vals):
        res = super(DistributionDeliveryNote, self).write(vals)
        # if 'tms_remark' in vals:
        #     for record in self:
        #         record.invoice_line_ids.write({'tms_remark': vals['tms_remark']})
        # if 'cancel_remark' in vals:
        #     for record in self:
        #         record.invoice_line_ids.write({'cancel_remark': vals['cancel_remark']})
        self._reset_sequence()
        return res


    def unlink(self):
        # Iterate over each record in the model
        for record in self:
            if record.invoice_line_ids:
                related_moves = self.env['account.move'].search([
                    ('id', 'in', record.invoice_line_ids.mapped('invoice_id.id'))
                ])
                # Clear the tms_remark field for each related move individually
                for move in related_moves:
                    move.write({'tms_remark': False})
                    move.write({'cancel_remark': False})
        
        # Call the original unlink method to delete the records
        return super(DistributionDeliveryNote, self).unlink()

    
    def _reset_sequence(self):
        for rec in self:
            current_sequence = 1
            for line in sorted(rec.invoice_line_ids, key=lambda x: (x.sequence, x.id)):
                line.sequence2 = current_sequence
                current_sequence += 1
    
    def action_update_tms_remark(self):
        """Called when user presses the Update button for TMS Remark"""
        for record in self:
            status = record.billing_status_remark
            for line in record.invoice_line_ids:
                # Only update line's TMS Remark if it matches current status
                if line.billing_status == status:
                    line.tms_remark = record.tms_remark

    def action_clear_tms_remark(self):
        """Clear all TMS Remarks in invoice lines"""
        for record in self:
            for line in record.invoice_line_ids:
                line.tms_remark = ''

    def action_update_cancel_remark(self):
        """Update cancel_remark to invoice lines matching cancel_status_remark"""
        for record in self:
            status = record.cancel_status_remark
            for line in record.invoice_line_ids:
                if line.billing_status == status:
                    line.cancel_remark = record.cancel_remark

    def action_clear_cancel_remark(self):
        """Clear all Cancel Remarks in invoice lines"""
        for record in self:
            for line in record.invoice_line_ids:
                line.cancel_remark = ''

class DistributionDeliveryNoteLine(models.Model):
    _name = "distribition.invoice.line"

    distribition_id = fields.Many2one("distribition.delivery.note")
    transport_line_id = fields.Many2one('delivery.round', related = 'distribition_id.transport_line_id',
                                        string = "สายส่ง TRL")
    company_round_id = fields.Many2one(related = 'invoice_id.company_round_id', string = "Mode of delivery",
                                       readonly = False)
    invoice_id = fields.Many2one('account.move', string = "Invoice",
                                 domain = "[('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('delivery_status', 'not in', ['sending', 'completed']), ('transport_line_id', '=', transport_line_id)]")
    name = fields.Char(related = 'invoice_id.name', string = "Invoice")
    invoice_date = fields.Date(related = 'invoice_id.invoice_date', string = "Invoice Date")
    partner_id = fields.Many2one('res.partner', related = 'invoice_id.partner_id', string = "Customer")
    spe_invoice = fields.Char(string = "SPE Invoice No")
    delivery_status = fields.Selection(
        [('sending', 'Sending'), ('resend', 'Resend'), ('completed', 'Completed'), ('cancel', 'Cancelled'), ],
        string = "Delivery Status")
    billing_status = fields.Selection([('none', 'None'), ('to_billing', 'To Billing'), ('to_finance', 'To Finance'), ],
                                      string = "Billing Status", default = 'none')
    cash_type = fields.Selection([('cash', 'สายเงินสด'), ('transfer', 'สายเงินโอน'), ],
                                 string = "สายส่งเงินสด / เงินโอน")
    sale_no = fields.Char(string = "SO No.")
    delivery_id = fields.Many2one('stock.picking', string = "Delivery No.")
    sale_person = fields.Many2one('res.users', string = "Sale Person")
    invoice_status = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancelled'), ],
                                      string = "Status")
    delivery_address_id = fields.Many2one('res.partner', string = "Delivery Address")
    submitted_date = fields.Date("Submitted Date")
    # invoice_date = fields.Date("Invoice Date")
    remark = fields.Char('Remark')
    tms_remark = fields.Char('TMS Remark')
    cancel_remark = fields.Char('Cancel Remark')
    note_for_receive = fields.Char('บันทึกขนส่งรับสินค้า')

    amount_total = fields.Float(string="Price", compute = "_compute_amount_total")

    sequence = fields.Integer(string="No", default=0)
    sequence2 = fields.Integer(string="No")

    def _compute_amount_total(self):
        for line in self:
            line.amount_total = (line.invoice_id.amount_total if line.invoice_id.amount_total else 0.0)

    @api.model
    def create(self, vals):
        res = super(DistributionDeliveryNoteLine, self).create(vals)
        res.invoice_id.is_tms = True
        sale_id = self.env['sale.order'].search([('name', '=', res.sale_no)])
        sale_id.is_tms = True
        if self.env.context.get("keep_line_sequence"):
            res.request_id._reset_sequence()
        return res
    
    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id.id:
            if not self.sale_no:
                rec_sale_order = self.env['sale.order'].search([('invoice_ids', '=', self.invoice_id.id)])
                self.sale_no = rec_sale_order.name
            if not self.sale_person:
                rec_account_move = self.env['account.move'].browse(self.invoice_id.id)
                self.sale_person = rec_account_move.invoice_user_id.id
            if not self.delivery_address_id:
                rec_account_move = self.env['account.move'].browse(self.invoice_id.id)
                self.delivery_address_id = rec_account_move.partner_shipping_id.id
    
    def change_billing_status(self):
        """Change the billing status of selected invoice lines to None"""
        selected_records = self.env['distribition.invoice.line'].browse(self.env.context.get('active_ids', []))
        for record in selected_records:
            if record.delivery_status == 'completed' and record.billing_status in ['to_billing', 'to_finance']:
                record.billing_status = 'none'
                if record.invoice_id:
                    record.invoice_id.billing_status = 'none'
                    record.invoice_id.to_finance = False
                    record.invoice_id.is_tms = False
            else:
                raise UserError(_("Cannot change billing status. Ensure delivery status is 'Completed' and billing status is either 'To Billing' or 'To Finance'."))

    def unlink(self):
        for record in self:
            record.invoice_id.is_tms = False
            record.invoice_id.to_finance = False
            record.invoice_id.billing_status = 'none'
        return super(DistributionDeliveryNoteLine, self).unlink()

class DistribitionDeliveryNoteLine(models.Model):
    _name = "distribition.delivery.note.line"
    _description = "Distribition Delivery Note Line"

    distribition_line_id = fields.Many2one("distribition.delivery.note")

    product_id = fields.Many2one('product.product', string = 'Product')
    name = fields.Char(related = 'product_id.name', string = "Product")
    branch_id = fields.Many2one('res.branch', string = "Branch")
    source_location = fields.Many2one('stock.location', string = "Source Location")
    qty_available = fields.Float(related = 'product_id.qty_available', string = 'On Hand', digits = (16, 2))
    qty_demand = fields.Float(string = "Demand", digits = (16, 2), readonly = True)
    qty_reserved = fields.Float(string = "Reserved", digits = (16, 2))
    qty_done = fields.Float(string = "Done", digits = (16, 2))
    uom_id = fields.Many2one("uom.uom", related = 'product_id.uom_id', string = "Unit of Measure")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_tms = fields.Boolean('To TMS')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_tms = fields.Boolean(related = 'sale_id.is_tms', string = 'To TMS')