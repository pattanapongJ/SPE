# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from shutil import move


class GenReceiptList(models.TransientModel):
    _name = 'gen.receipt.list'
    _description = "Generate Receipt Lists"

    name = fields.Char(string="Name", default="Generate Receipt Lists", required=True)
    partner_id = fields.Many2one('res.partner', string='Supplier', required=True, domain=[('supplier', '=', True)])
    company_id = fields.Many2one("res.company", string="Company", required=True)
    purchase_ids = fields.Many2many('purchase.order', string='PO NO', domain=[('check_done_picking', '=', False)])
    picking_ids = fields.Many2many('stock.picking', string='Receipt NO')
    purchase_type = fields.Many2one('purchase.order.type', string='PO Type', required=True, domain= [('is_in_out', '=', True)])
    s_date_form = fields.Datetime(string='Scheduled Date From')
    s_date_to = fields.Datetime(string='Scheduled Date To')
    d_date_form = fields.Datetime(string='Deadline Date From')
    d_date_to = fields.Datetime(string='Deadline Date To')
    performa_invoice = fields.Char(string='Performa Invoice(PI)')
    per_invoice_date_form = fields.Date(string='Performa Invoice Date From')
    per_invoice_date_to = fields.Date(string='Performa Invoice Date To')
    commercial_invoice = fields.Char(string='Commercial Invoice(CI)')
    com_invoice_date_form = fields.Date(string='Commercial Invoice Date From')
    com_invoice_date_to = fields.Date(string='Commercial Invoice Date To')
    vendor_ref = fields.Char(string='Vendor Reference')
    po_ref = fields.Char(string='PO Reference')
    untaxed_amount = fields.Float(string='Untaxed', compute='_compute_amount')
    vat_amount = fields.Float(string='Vat', compute='_compute_amount')
    total_amount = fields.Float(string='Total', compute='_compute_amount')
    receipt_list_id = fields.Many2one('receipt.list', string='Receipt list')
    
    line_ids = fields.One2many('gen.receipt.list.line', 'gen_receipt_list_id', string='Line')

    def _compute_amount(self):
        for record in self:
            record.untaxed_amount = sum(record.line_ids.mapped('subtotal'))
            record.vat_amount = sum(record.line_ids.mapped('price_tax'))
            record.total_amount = sum(record.line_ids.mapped('net_price'))

    def search_value(self):
        value = [('picking_type_id.code', '=', 'incoming'),('product_uom_qty', '>', 0),('state', 'not in', ('done', 'cancel', 'skip_done')),('receipt_list_line_id', '=', False)]
        value_po = [('product_id.type', '=', 'service'),('order_id.state', 'in', ('done', 'purchase')),('service_list_id', '=', False)]
        # Filter by supplier
        if self.company_id:
            value.append(('company_id', '=', self.company_id.id))
            value_po.append(('company_id', '=', self.company_id.id))

        if self.partner_id:
            value.append(('picking_id.partner_id', '=', self.partner_id.id))
            value_po.append(('partner_id', '=', self.partner_id.id))
        
        # Filter by purchase orders
        if self.purchase_ids:
            value.append(('purchase_line_id.order_id', 'in', self.purchase_ids.ids))
            value_po.append(('order_id', 'in', self.purchase_ids.ids))
        
        # Filter by pickings
        if self.picking_ids:
            value.append(('picking_id', 'in', self.picking_ids.ids))
        
        # Filter by purchase type
        if self.purchase_type:
            value.append(('purchase_line_id.order_id.order_type', 'in', self.purchase_type.ids))
            value_po.append(('order_id.order_type', 'in', self.purchase_type.ids))
        
        # Filter by scheduled date
        if self.s_date_form:
            value.append(('date_expected', '>=', self.s_date_form))
            value_po.append(('order_id.date_order', '>=', self.s_date_form))
        if self.s_date_to:
            value.append(('date_expected', '<=', self.s_date_to))
            value_po.append(('order_id.date_order', '<=', self.s_date_to))
        
        # Filter by deadline date
        if self.d_date_form:
            value.append(('date_deadline', '>=', self.d_date_form))
            value_po.append(('order_id.date_order', '>=', self.d_date_form))
        if self.d_date_to:
            value.append(('date_deadline', '<=', self.d_date_to))
            value_po.append(('order_id.date_order', '<=', self.d_date_to))

        if self.performa_invoice:
            value.append(('purchase_line_id.order_id.performa_invoice', 'ilike', self.performa_invoice))
            value_po.append(('order_id.performa_invoice', 'ilike', self.performa_invoice))
        if self.per_invoice_date_form:
            value.append(('purchase_line_id.order_id.performa_invoice_date', '>=', self.per_invoice_date_form))
            value_po.append(('order_id.performa_invoice_date', '>=', self.per_invoice_date_form))
        if self.per_invoice_date_to:
            value.append(('purchase_line_id.order_id.performa_invoice_date', '<=', self.per_invoice_date_to))
            value_po.append(('order_id.performa_invoice_date', '<=', self.per_invoice_date_to))
        
        if self.commercial_invoice:
            value.append(('purchase_line_id.order_id.commercial_invoice', 'ilike', self.commercial_invoice))
            value_po.append('order_id.commercial_invoice', 'ilike', self.commercial_invoice)
        if self.com_invoice_date_form:
            value.append(('purchase_line_id.order_id.commercial_invoice_date', '>=', self.com_invoice_date_form))
            value_po.append(('order_id.commercial_invoice_date', '>=', self.com_invoice_date_form))
        if self.com_invoice_date_to:
            value.append(('purchase_line_id.order_id.commercial_invoice_date', '<=', self.com_invoice_date_to))
            value_po.append(('order_id.commercial_invoice_date', '<=', self.com_invoice_date_to))

        if self.vendor_ref:
            value.append(('purchase_line_id.order_id.partner_ref', 'ilike', self.vendor_ref))
            value_po.append(('order_id.partner_ref', 'ilike', self.vendor_ref))
        if self.po_ref:
            value.append(('purchase_line_id.order_id.po_reference', 'ilike', self.po_ref))
            value_po.append(('order_id.po_reference', 'ilike', self.po_ref))
    
        move_po = self.env['stock.move'].search(value)
        
        move_po_service = self.env['purchase.order.line'].search(value_po)
        # Clear existing lines
        self.line_ids.unlink()
        
        # Create new lines
        lines = []
        for move in move_po:
            lines.append((0, 0, {
                'move_id': move.id,
                'remark': move.purchase_line_id.remark_1
            }))
        for move in move_po_service:
            lines.append((0, 0, {
                'purchase_line_id': move.id,
                'remark': move.remark_1
            }))

        self.line_ids = lines
    
    def clear_value(self):
        self.line_ids.unlink()

    def confirm_add_item(self):
        line_value = [(0, 0, {
                'move_id': line.move_id.id,
                'shipped_qty': line.demand,
                'price': line.price,
                'remark': line.remark,
            }) for line in self.line_ids if line.select and line.move_id]
        line_service = [(0, 0, {
                'purchase_line_id': line.purchase_line_id.id
            }) for line in self.line_ids if line.select and line.purchase_line_id]
        self.receipt_list_id.write({'line_ids': line_value,
            'line_service_ids': line_service})

    def create_receipt_lists(self):
        
        line_value = [(0, 0, {
                'move_id': line.move_id.id,
                'shipped_qty': line.demand,
                'price': line.price,
                'remark': line.remark,
            }) for line in self.line_ids if line.select and line.move_id]
        
        line_service = [(0, 0, {
                'purchase_line_id': line.purchase_line_id.id
            }) for line in self.line_ids if line.select and line.purchase_line_id]
        if line_value or line_service:
            po_ids = self.line_ids.sorted(key=lambda r: r.date).mapped('move_id.purchase_line_id.order_id')
            po_id = po_ids[0] if po_ids else False
            value = {
                'partner_id': self.partner_id.id,
                'user_em_id': self.env.user.employee_id.id,
                'company_id': self.company_id.id,
                'purchase_type': self.purchase_type.id,
                'operation_type': self.purchase_type.picking_type_id.id,
                'warehouse_id': self.purchase_type.picking_type_id.warehouse_id.id,
                'location_id': self.purchase_type.picking_type_id.default_location_dest_id.id,
                'scheduled_date': max(self.line_ids.mapped('move_id.date')) if self.line_ids.mapped('move_id.date') else False,
                'receipted_date': max(self.line_ids.mapped('date') if self.line_ids.mapped('date') else False),
                'line_ids': line_value,
                'line_service_ids': line_service,
            }
            if po_id:
                value.update({
                    'performa_invoice': po_id.performa_invoice,
                    'per_invoice_date': po_id.performa_invoice_date,
                    'commercial_invoice': po_id.commercial_invoice,
                    'com_invoice_date': po_id.commercial_invoice_date,
                    'vendor_ref': po_id.partner_ref,
                    'po_ref': po_id.name,
                    'incoterm_id': po_id.incoterm_id.id,
                    'etd': po_id.etd_date,
                    'eta': po_id.eta_date,
                    'delivery_mode': po_id.carrier_id.id,
                    'original_country': po_id.country_orinal.id,
                    'currency_id': po_id.currency_id.id,
                    'shipper': po_id.shipper,
                })
            create_receipt_lists = self.env['receipt.list'].create(value)
            self.line_ids.unlink()

            return {
                'name': _('Receipt List'),
                'view_mode': 'form',
                'res_model': 'receipt.list',
                'res_id': create_receipt_lists.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
        else:
            raise ValidationError("No items selected.")
    
    def select_all(self):
        for line in self.line_ids:
            line.select = True

class GenReceiptListLine(models.TransientModel):
    _name = 'gen.receipt.list.line'
    _description = "Generate Receipt Lists Line"

    name = fields.Char(string="Description")
    select = fields.Boolean(string="Select", default=False)
    gen_receipt_list_id = fields.Many2one('gen.receipt.list', string='Gen Receipt List', ondelete="cascade")
    move_id = fields.Many2one('stock.move', string='Move')
    product_id = fields.Many2one('product.product', compute='_compute_data', string="Product")
    purchase_line_id = fields.Many2one('purchase.order.line', string='purchase line')
    name = fields.Char(compute='_compute_data', string="Description")
    date = fields.Datetime(compute='_compute_data', string="Receipted Date")
    warehouse_id = fields.Many2one(related="move_id.warehouse_id", string="Warehouse", store=True)
    location_dest_id = fields.Many2one(related="move_id.location_dest_id", string="Location", store=True)
    reference = fields.Char(compute='_compute_data', string="Receipt No", store=True)
    group_id = fields.Many2one(related="move_id.group_id", string="PO No", store=True)
    demand_total = fields.Float(compute='_compute_data', string="PO Demand")
    demand = fields.Float(related="move_id.product_uom_qty", string="Remain")
    price_tax = fields.Float(compute='_compute_data', string='Tax', store=True)
    shipped_qty = fields.Float(string="Shipped")
    price = fields.Float(compute='_compute_data', string="Unit Price")
    subtotal = fields.Monetary(compute='_compute_data', string="Subtotal")
    state = fields.Selection(related="move_id.state", string="Status")

    default_code = fields.Char(related="move_id.product_id.default_code", string="Internal Reference")
    barcode = fields.Char(related="move_id.product_id.barcode", string="Barcode")
    product_categ_id = fields.Many2one(related="move_id.product_uom_category_id", string="Product Category")
    product_tag_ids = fields.Many2many(related="move_id.tags_product_sale_ids", string="Product Tags")
    all_stock = fields.Float(related="move_id.product_id.qty_available", string="All Stock")
    available_stock = fields.Float(related="move_id.product_id.free_qty", string="Available Stock")
    external_barcodes = fields.One2many(related="move_id.product_id.barcode_spe_ids", string="External Barcode")
    remark = fields.Char(string="Remarks")
    hs_code = fields.Many2one(related="move_id.product_id.hs_code_id", string="HS Code")
    box = fields.Integer(related="move_id.product_id.box", string="กล่องละ")
    crate = fields.Integer(related="move_id.product_id.crate", string="ลังละ")
    net_price = fields.Monetary(compute='_compute_data', string="Net Price")
    std_price = fields.Float(string="Std Price")
    discount = fields.Char(compute='_compute_data', string="Discount")
    taxes_id = fields.Many2many('account.tax',compute='_compute_data', string="Taxes")
    currency_id = fields.Many2one('res.currency',compute='_compute_data', string="Currency")


    def action_remove_line(self):
        self.unlink()
        
    def _compute_data(self):
        for rec in self:
            if rec.move_id:
                rec.name = rec.move_id.product_id.display_name
                rec.product_id = rec.move_id.product_id.id
                rec.reference = rec.move_id.reference
                rec.date = rec.move_id.date
                rec.price_tax = rec.move_id.purchase_line_id.price_tax
                rec.subtotal = rec.shipped_qty * rec.move_id.purchase_line_id.price_unit 
                # rec.remark = rec.move_id.purchase_line_id.remark_1
                rec.net_price = rec.move_id.purchase_line_id.price_total
                rec.discount = rec.move_id.purchase_line_id.multi_disc
                rec.taxes_id = rec.move_id.purchase_line_id.taxes_id.ids
                rec.currency_id = rec.move_id.purchase_line_id.currency_id.id
                rec.demand_total = rec.move_id.demand_total
                rec.price = rec.move_id.purchase_line_id.price_unit  
            else:
                rec.name = rec.purchase_line_id.product_id.display_name
                rec.product_id = rec.purchase_line_id.product_id.id
                rec.reference = rec.purchase_line_id.order_id.name
                rec.date = rec.purchase_line_id.date_planned
                rec.price_tax = rec.purchase_line_id.price_tax
                rec.subtotal = rec.shipped_qty * rec.purchase_line_id.price_unit 
                # rec.remark = rec.purchase_line_id.remark_1
                rec.net_price = rec.purchase_line_id.price_total
                rec.discount = rec.purchase_line_id.multi_disc
                rec.taxes_id = rec.purchase_line_id.taxes_id.ids
                rec.currency_id = rec.purchase_line_id.currency_id.id
                rec.demand_total = rec.purchase_line_id.product_qty
                rec.price = rec.purchase_line_id.price_unit 
        

