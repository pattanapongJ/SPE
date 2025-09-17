# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class GenBillingReceiptList(models.TransientModel):
    _name = 'gen.billing.rl'
    _description = "Generate Billing Receipt List"

    name = fields.Char(string="Name", default="Generate Billing Receipt List", required=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, domain=[('supplier', '=', True)])
    vendor_ref = fields.Char(string='Vendor Reference')
    purchase_ids = fields.Many2many('purchase.order', string='PO NO', domain= [('invoice_status', '!=', 'invoiced')])
    purchase_type = fields.Many2one('purchase.order.type', string='PO Type', domain= [('is_in_out', '=', True)])
    is_service = fields.Boolean(string="Service")

    receipt_list_ids = fields.Many2many('receipt.list', string='RL No', domain= [('invoice_status', '!=', 'invoiced')])
    rl_date_form = fields.Datetime(string='Receipt Date From')
    rl_date_to = fields.Datetime(string='Receipt Date To')
    performa_invoice = fields.Char(string='Performa Invoice(PI)')
    per_invoice_date_form = fields.Date(string='Performa Invoice Date From')
    per_invoice_date_to = fields.Date(string='Performa Invoice Date To')
    commercial_invoice = fields.Char(string='Commercial Invoice(CI)')
    com_invoice_date_form = fields.Date(string='Commercial Invoice Date From')
    com_invoice_date_to = fields.Date(string='Commercial Invoice Date To')
    picking_ids = fields.Many2many('stock.picking', string='Receipt NO')

    company_id = fields.Many2one("res.company", string="Company", required=True)

    untaxed_amount = fields.Float(string='Untaxed', compute='_compute_amount')
    vat_amount = fields.Float(string='Vat', compute='_compute_amount')
    total_amount = fields.Float(string='Total', compute='_compute_amount')

    receipt_done_type = fields.Selection([
        ('rl', 'Receipt List(RL)'),
        ('rt', 'Receipt Transfer(IN)')
    ], string='Receipt Done by', default='rl')
    
    line_ids = fields.One2many('gen.billing.rl.line', 'gen_billing_rl_id', string='Line')

    @api.onchange('receipt_list_ids', 'picking_ids')
    def _onchange_receipt_list_ids(self):
        for record in self:
            if record.purchase_type:
                if record.receipt_list_ids:
                    for receipt_list in record.receipt_list_ids:
                        if record.purchase_type != receipt_list.purchase_type:
                            raise UserError(_("Purchase Type must be the same."))
                        
                if record.picking_ids:
                    for picking in record.picking_ids:
                        for move_lines in picking.move_lines:
                            if record.purchase_type != move_lines.purchase_line_id.order_id.order_type:
                                raise UserError(_("Purchase Type must be the same."))
                if not record.receipt_list_ids and not record.picking_ids:
                    record.purchase_type = False
            else:
                if record.receipt_list_ids:
                    for receipt_list in record.receipt_list_ids:
                        record.purchase_type = receipt_list.purchase_type.id
                        break
                elif record.picking_ids:
                    for picking in record.picking_ids:
                        for move_lines in picking.move_lines:
                            record.purchase_type = move_lines.purchase_line_id.order_id.order_type.id
                            break
            # Partner & Company set 
            if not record.partner_id:
                if record.receipt_list_ids:
                    record.partner_id = record.receipt_list_ids[0].partner_id.id
                elif record.picking_ids:
                    record.partner_id = record.picking_ids[0].partner_id.id
            if not record.company_id:
                if record.receipt_list_ids:
                    record.company_id = record.receipt_list_ids[0].company_id.id
                elif record.picking_ids:
                    record.company_id = record.picking_ids[0].company_id.id

            # Partner & Company check
            partner_ref = record.partner_id
            company_ref = record.company_id

            for receipt_list in record.receipt_list_ids:
                if receipt_list.partner_id != partner_ref:
                    raise UserError(_("กรุณาตรวจสอบข้อมูล Supplier/ Vendor ที่เลือกมาไม่ตรงกันค่ะ"))
                if receipt_list.company_id != company_ref:
                    raise UserError(_("กรุณาตรวจสอบข้อมูล Company ที่เลือกมาไม่ตรงกันค่ะ"))

            for picking in record.picking_ids:
                if picking.partner_id != partner_ref:
                    raise UserError(_("กรุณาตรวจสอบข้อมูล Supplier/ Vendor ที่เลือกมาไม่ตรงกันค่ะ"))
                if picking.company_id != company_ref:
                    raise UserError(_("กรุณาตรวจสอบข้อมูล Company ที่เลือกมาไม่ตรงกันค่ะ"))

    def _compute_amount(self):
        for record in self:
            record.untaxed_amount = sum(record.line_ids.mapped('subtotal'))
            record.vat_amount = sum(record.line_ids.mapped('price_tax'))
            record.total_amount = sum(record.line_ids.mapped('net_price'))

    def search_value(self):
        if not self.purchase_type:
            raise UserError(_("Please select Purchase Type."))
        value_move = [('purchase_line_id.qty_to_invoice', '>', 0),('purchase_line_id', '!=', False),('state', 'in', ('done','skip_done')),('receipt_list_line_id', '=', False)]
        value = [('state', '=', 'done'),('qty_to_invoice', '>', 0)]
        value_service = [('receipt_list_id.state', '=', 'done'),('po_id.invoice_status', '!=', 'invoiced')]
        if self.receipt_list_ids:
            value.append(('receipt_list_id.id', 'in', self.receipt_list_ids.ids))
            value_service.append(('receipt_list_id.id', 'in', self.receipt_list_ids.ids))

        if self.company_id:
            value_move.append(('company_id', '=', self.company_id.id))
            value.append(('receipt_list_id.company_id', '=', self.company_id.id))
            value_service.append(('receipt_list_id.company_id', '=', self.company_id.id))
        
        if self.is_service:
            value.append(('receipt_list_id.line_service_ids', '!=', False))
            value_service.append(('receipt_list_id.line_service_ids', '!=', False))
        
        if self.partner_id:
            value_move.append(('picking_id.partner_id', '=', self.partner_id.id))
            value.append(('receipt_list_id.partner_id', '=', self.partner_id.id))
            value_service.append(('receipt_list_id.partner_id', '=', self.partner_id.id))
        
        # Filter by purchase orders
        if self.purchase_ids:
            value_move.append(('purchase_line_id.order_id', 'in', self.purchase_ids.ids))
            value.append(('move_id.purchase_line_id.order_id', 'in', self.purchase_ids.ids))
            value_service.append(('po_id', 'in', self.purchase_ids.ids))
        
        # Filter by pickings
        if self.picking_ids:
            value_move.append(('picking_id', 'in', self.picking_ids.ids))
            value.append(('move_id.picking_id', 'in', self.picking_ids.ids))
        
        # Filter by purchase type
        if self.purchase_type:
            value_move.append(('purchase_line_id.order_id.order_type', 'in', self.purchase_type.ids))
            value.append(('receipt_list_id.purchase_type', 'in', self.purchase_type.ids))
            value_service.append(('receipt_list_id.purchase_type', 'in', self.purchase_type.ids))
        
        # Filter by rl date
        if self.rl_date_form:
            value_move.append(('date_expected', '>=', self.s_date_form))
            value.append(('create_date', '>=', self.rl_date_form))
            value_service.append(('create_date', '>=', self.rl_date_form))
        if self.rl_date_to:
            value_move.append(('date_expected', '<=', self.s_date_to))
            value.append(('create_date', '<=', self.rl_date_to))
            value_service.append(('create_date', '<=', self.rl_date_to))
    
        if self.performa_invoice:
            value_move.append(('purchase_line_id.order_id.performa_invoice', 'ilike', self.performa_invoice))
            value.append(('receipt_list_id.performa_invoice', 'ilike', self.performa_invoice))
            value_service.append(('receipt_list_id.performa_invoice', 'ilike', self.performa_invoice))
        if self.per_invoice_date_form:
            value_move.append(('purchase_line_id.order_id.performa_invoice_date', '>=', self.per_invoice_date_form))
            value.append(('receipt_list_id.performa_invoice_date', '>=', self.per_invoice_date_form))
            value_service.append(('receipt_list_id.performa_invoice_date', '>=', self.per_invoice_date_form))
        if self.per_invoice_date_to:
            value_move.append(('purchase_line_id.order_id.performa_invoice_date', '<=', self.per_invoice_date_to))
            value.append(('receipt_list_id.performa_invoice_date', '<=', self.per_invoice_date_to))
            value_service.append(('receipt_list_id.performa_invoice_date', '<=', self.per_invoice_date_to))
        
        if self.commercial_invoice:
            value_move.append(('purchase_line_id.order_id.commercial_invoice', 'ilike', self.commercial_invoice))
            value.append(('receipt_list_id.commercial_invoice', 'ilike', self.commercial_invoice))
            value_service.append(('receipt_list_id.commercial_invoice', 'ilike', self.commercial_invoice))
        if self.com_invoice_date_form:
            value_move.append(('purchase_line_id.order_id.commercial_invoice_date', '>=', self.com_invoice_date_form))
            value.append(('receipt_list_id.commercial_invoice_date', '>=', self.com_invoice_date_form))
            value_service.append(('receipt_list_id.commercial_invoice_date', '>=', self.com_invoice_date_form))
        if self.com_invoice_date_to:
            value_move.append(('purchase_line_id.order_id.commercial_invoice_date', '<=', self.com_invoice_date_to))
            value.append(('receipt_list_id.commercial_invoice_date', '<=', self.com_invoice_date_to))
            value_service.append(('receipt_list_id.commercial_invoice_date', '<=', self.com_invoice_date_to))

        if self.vendor_ref:
            value_move.append(('purchase_line_id.order_id.partner_ref', 'ilike', self.vendor_ref))
            value.append(('receipt_list_id.partner_ref', 'ilike', self.vendor_ref))
            value_service.append(('receipt_list_id.partner_ref', 'ilike', self.vendor_ref))
       
        if self.receipt_done_type == 'rl':
            move_list = self.env['receipt.list.line'].search(value)

            move_list_service = self.env['receipt.list.line.service'].search(value_service)
        else:
            move_list = self.env['stock.move'].search(value_move)
        
        # Clear existing lines
        self.line_ids.unlink()
        
        # Create new lines
        lines = []
        if self.receipt_done_type == 'rl':
            for move in move_list:
                lines.append((0, 0, {
                    'receipt_list_line_id': move.id,
                }))
            for move_ser in move_list_service:
                lines.append((0, 0, {
                    'service_list_id': move_ser.id,
                }))
        else:
            for move in move_list:
                lines.append((0, 0, {
                    'move_id': move.id,
                }))
        self.line_ids = lines
    
    def clear_value(self):
        self.line_ids.unlink()


    def create_bills(self):
        ac_moves = []
        line_ids = self.line_ids.filtered(lambda m: m.select == True)
      
        if line_ids:
            purchase_id = line_ids[0].purchase_line_id.order_id
            ac_moves.append(purchase_id.action_create_invoice_rl(line_ids).id)

            result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
            result['domain'] = [('id', 'in', ac_moves)]
            self.line_ids.unlink()
            return result
        else:
            raise ValidationError(_('No line selected.'))
    
    
    def select_all(self):
        for line in self.line_ids:
            line.select = True

class GenBillingReceiptListLine(models.TransientModel):
    _name = 'gen.billing.rl.line'
    _description = "Generate Billing Receipt List Line"

    name = fields.Char(string="Description")
    select = fields.Boolean(string="Select", default=False)
    gen_billing_rl_id = fields.Many2one('gen.billing.rl', string='Gen Receipt List', ondelete="cascade")
    receipt_list_line_id = fields.Many2one('receipt.list.line', string='Receipt List line')
    service_list_id = fields.Many2one('receipt.list.line.service', string='Service List line')
    purchase_line_id = fields.Many2one('purchase.order.line',compute='_compute_data', string='purchase line')
    receipt_list_id = fields.Many2one(related="receipt_list_line_id.receipt_list_id")
    move_id = fields.Many2one('stock.move', string='stock move')
    product_id = fields.Many2one('product.product', compute='_compute_data')
    date = fields.Datetime(related="move_id.purchase_line_id.date_planned")
    warehouse_id = fields.Many2one('stock.warehouse')
    location_dest_id = fields.Many2one('stock.location')

    reference = fields.Char(compute='_compute_data', string="Receipt No")
    group_id = fields.Many2one("procurement.group")
    batch_no = fields.Char(related="receipt_list_line_id.batch_no")
    demand_total = fields.Float(compute='_compute_data')
    demand = fields.Float("PO Remain")
    po_product_uom = fields.Many2one(related='purchase_line_id.product_uom', string='PO Unit of Measure')
    shipped_qty = fields.Float("PO Shipped")
    receipt_qty = fields.Float(related="receipt_list_line_id.receipt_qty")
    receipt_done = fields.Float(compute='_compute_data')
    qty_to_invoice = fields.Float(compute='_compute_data')
    taxes_id = fields.Many2many(related='move_id.taxes_id', string='Taxes')
    price_tax = fields.Float(compute='_compute_amount', string='Tax')
    discount = fields.Char(related="purchase_line_id.multi_disc")
    std_price = fields.Float(string="Std Price",related="product_id.lst_price")
    duty = fields.Float(related="product_id.hs_code_id.duty", string="Duty")
    price = fields.Float(compute='_compute_data')
    subtotal = fields.Monetary(compute='_compute_data')
    net_price = fields.Monetary("Net Amount",compute='_compute_data')
    default_code = fields.Char(related="product_id.default_code")
    barcode = fields.Char(related="product_id.barcode")
    product_categ_id = fields.Many2one(related="product_id.categ_id")
    product_tag_ids = fields.Many2many(related="move_id.tags_product_sale_ids")
    all_stock = fields.Float(related="product_id.qty_available")
    available_stock = fields.Float(related="product_id.free_qty")
    external_barcodes = fields.One2many(related="product_id.barcode_spe_ids")
    remark = fields.Char(related="receipt_list_line_id.remark")
    hs_code = fields.Many2one(related="product_id.hs_code_id")
    box = fields.Integer(related="product_id.box")
    crate = fields.Integer(related="product_id.crate")

    state = fields.Selection(related="receipt_list_line_id.state")
    currency_id = fields.Many2one('res.currency', compute='_compute_data')

    def action_remove_line(self):
        self.unlink()

    def _compute_data(self):
        for rec in self:
            if rec.receipt_list_line_id or rec.service_list_id:
                if rec.receipt_list_line_id:
                    rec.move_id = rec.receipt_list_line_id.move_id.id
                    rec.purchase_line_id = rec.receipt_list_line_id.move_id.purchase_line_id.id
                    rec.product_id = rec.receipt_list_line_id.product_id.id
                    rec.demand_total = rec.receipt_list_line_id.demand_total
                    rec.price = rec.receipt_list_line_id.price
                    rec.receipt_done = rec.receipt_list_line_id.po_receipt_done
                    rec.subtotal = rec.receipt_list_line_id.subtotal
                    rec.currency_id = rec.receipt_list_line_id.currency_id.id
                    rec.qty_to_invoice = rec.receipt_list_line_id.qty_to_invoice
                    rec.reference = rec.receipt_list_line_id.reference
                    rec.price_tax = rec.receipt_list_line_id.price_tax
                    rec.net_price = rec.receipt_list_line_id.net_price
                    rec.shipped_qty = rec.receipt_list_line_id.po_shipped_qty
                    rec.demand = rec.receipt_list_line_id.po_remain
                    rec.warehouse_id = rec.receipt_list_line_id.warehouse_id.id
                    rec.location_dest_id = rec.receipt_list_line_id.location_dest_id.id
                    rec.group_id = rec.receipt_list_line_id.group_id.id
                else:
                    rec.purchase_line_id = rec.service_list_id.purchase_line_id.id
                    rec.product_id = rec.service_list_id.product_id.id
                    rec.demand_total = rec.service_list_id.demand
                    rec.receipt_done = rec.service_list_id.demand
                    rec.price = rec.service_list_id.price
                    rec.qty_to_invoice = rec.service_list_id.demand
                    rec.subtotal = rec.service_list_id.subtotal
                    rec.currency_id = rec.service_list_id.currency_id.id
                    rec.reference = rec.service_list_id.po_id.name
                    rec.shipped_qty = rec.service_list_id.demand
                    rec.net_price = rec.service_list_id.purchase_line_id.price_total
                    rec.price_tax = rec.service_list_id.purchase_line_id.price_total - rec.service_list_id.purchase_line_id.price_subtotal
            else:
                rec.purchase_line_id = rec.move_id.purchase_line_id.id
                rec.product_id = rec.move_id.product_id.id
                rec.demand_total = rec.move_id.demand_total
                rec.receipt_done = rec.move_id.po_quantity_done
                rec.price = rec.move_id.purchase_line_id.price_unit
                rec.subtotal = rec.move_id.purchase_line_id.price_subtotal
                rec.currency_id = rec.move_id.currency_id.id
                rec.qty_to_invoice = rec.move_id.purchase_line_id.qty_to_invoice
                rec.reference = rec.move_id.reference
                rec.price_tax = rec.move_id.price_tax
                rec.net_price = rec.move_id.net_price
                rec.shipped_qty = rec.move_id.po_qty_counted
                rec.group_id = rec.move_id.group_id.id
                rec.demand = sum(self.env['stock.move'].search([('product_id', '=', rec.product_id.id),('state', 'not in', ('done','cancel')),('group_id', '=', rec.group_id.id)]).mapped('po_remain'))
                rec.warehouse_id = rec.move_id.location_dest_id.warehouse_id.id
                rec.location_dest_id = rec.move_id.location_dest_id.id
                