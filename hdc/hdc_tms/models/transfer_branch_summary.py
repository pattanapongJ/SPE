# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta

class ReSupplyTransferBranchSummary(models.Model):
    _name = "resupply.transfer.branch.summary"
    _description = "Transfer Branch Summary"

    name = fields.Char(string="Transfer Branch Summary", readonly=True, default='Transfer Branch Summary')
    operation_type_id = fields.Many2one('stock.picking.type', string="Operation Type" , domain=[('code', '=', 'outgoing')])
    

    scheduled_date_start = fields.Date("Delivery Date", default=lambda self: fields.Date.today(), required=True)
    scheduled_date_end = fields.Date(
        "Delivery Date",
        default=lambda self: fields.Date.today() ,required=True
    )

    sale_order_ids = fields.Many2many('sale.order',string="Sale Order No",
        domain=lambda self: [
            ('state', '=', 'sale'), ('is_tms', '=', False)
        ])
    delivery_order_ids = fields.Many2many('stock.picking',string="Delivery Order No",
        domain=lambda self: [
            ('state', '=', 'done'),
            ('is_tms', '=', False), ('picking_type_code', '=', 'outgoing')
        ])
    invoice_ids = fields.Many2many(
        'account.move',
        'transfer_branch_invoice_rel',
        'transfer_id',
        'invoice_id',
        string="Invoices No", 
        domain=lambda self: [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('is_tms', '=', False)
        ])
    available_invoice_ids = fields.Many2many(
        'account.move',
        compute='_compute_available_invoices',
        store=False,
    )
    spe_invoice_ids = fields.Many2many(
        'account.move',
        'transfer_branch_spe_invoice_rel',
        'transfer_id',
        'spe_invoice_id',
        string="SPE Invoice",
        domain="[('id', 'in', available_invoice_ids)]"
    )

    partner_ids = fields.Many2many(
        'res.partner',
        'transfer_branch_partner_rel',
        'transfer_id',
        'partner_id',
        string="Customer",
    )
    
    @api.depends('invoice_ids', 'spe_invoice_ids')
    def _compute_available_invoices(self):
        for rec in self:
            domain = [('form_no', '!=', False),('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('is_tms', '=', False)]
            if rec.invoice_ids:
                domain = ['|'] + domain + [
                    ('id', 'in', rec.invoice_ids.ids),
                    ('old_spe_invoice', 'in', rec.invoice_ids.mapped('form_no')),
                ]
            elif rec.spe_invoice_ids:
                domain = ['|'] + domain + [
                    ('form_no', 'in', rec.spe_invoice_ids.mapped('form_no')),
                    ('old_spe_invoice', 'in', rec.spe_invoice_ids.mapped('form_no')),
                ]
            rec.available_invoice_ids = self.env['account.move'].search(domain).ids

    @api.onchange('invoice_ids')
    def _onchange_invoice_ids(self):
        """Update domain for spe_invoice_ids based on selected invoices"""
        domain = [('form_no', '!=', False),('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('is_tms', '=', False)]
        if self.invoice_ids:
            domain = ['|'] + domain + [
                ('id', 'in', self.invoice_ids.ids),
                ('old_spe_invoice', 'in', self.invoice_ids.mapped('form_no')),
            ]
        
        return {'domain': {'spe_invoice_ids': domain}}

    transport_line_ids = fields.Many2many('delivery.round', string="สายส่ง TRL")
    company_round_ids = fields.Many2many('company.delivery.round', string="Mode of delivery")
    company_id = fields.Many2one("res.company", string="Company")

    summary_line_ids = fields.One2many('search.branch.summary.line', 'search_id', string="Product Lines")
    invoice_line_ids = fields.One2many('search.invoice.line', 'search_id', string="Invoices Lines")
    is_create = fields.Boolean('Can Create Delivery Noted', compute="_compute_is_create")

    def _compute_is_create(self):
        for rec in self:
            rec.is_create = True if len(rec.invoice_line_ids) > 0 else False

    @api.onchange('operation_type_id')
    def onchange_operation_type_id(self):
        if self.operation_type_id:
            domain = [('picking_type_id', '=', self.operation_type_id.id), ('state', '=', 'done')]
            return {'domain': {'delivery_order_ids': domain}}
        else:
            return {'domain': {'delivery_order_ids': []}}

    def search_action(self):
        domain_search = [('is_tms', '=', False),('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('delivery_status', 'not in', ['sending', 'completed'])]
        if self.scheduled_date_start:
            if self.scheduled_date_end and self.scheduled_date_end < self.scheduled_date_start:
                raise UserError(_("The end date cannot be less than the start date."))
            datetime_start = (self.scheduled_date_start - relativedelta(days=1)).strftime("%Y-%m-%d 17:00:00")
            domain_search += [('invoice_date', '>=', datetime_start)]
        
        if self.scheduled_date_end :
            datetime_end = (self.scheduled_date_end).strftime("%Y-%m-%d 16:59:59")
            domain_search += [('invoice_date', '<=', datetime_end)]
        
        if self.invoice_ids:
            domain_search += [('id', 'in', self.invoice_ids.ids)]
        
        if self.transport_line_ids:
            domain_search += [('transport_line_id', 'in', self.transport_line_ids.ids)]
        
        if self.company_round_ids:
            domain_search += [('company_round_id', 'in', self.company_round_ids.ids)]

        if self.company_id:
            domain_search += [('company_id', '=', self.company_id.id)]
        if self.partner_ids:
            partner_ids = []
            for partner_id in self.partner_ids:
                # เพิ่ม partner หลัก
                partner_ids.append(partner_id.id)
                # เพิ่ม child partners (branches, contacts, etc.)
                child_partners = self.env['res.partner'].search([('parent_id', '=', partner_id.id)])
                if child_partners:
                    partner_ids.extend(child_partners.ids)

            domain_search += [('partner_id', 'in', partner_ids)]

        source = []
        if self.sale_order_ids:
            for order_id in self.sale_order_ids:
                if order_id.name not in source:
                    source += [order_id.name]

        if self.delivery_order_ids:

            for order_id in self.delivery_order_ids:
                if order_id.origin not in source:
                    source += [order_id.origin]

        if len(source) > 0:
            domain_search += [('invoice_origin', 'in', source)]

        transfer_search_config = self.env['account.move'].search(domain_search + [])
        self.invoice_line_ids.unlink()

        order_line = []
        for transfer in transfer_search_config:
            delivery_id = False
            if transfer.invoice_origin:
                sale_id = self.env['sale.order'].search([("name", "=", transfer.invoice_origin)])
                delivery_id = sale_id.picking_ids[-1] if sale_id.picking_ids else False

            line = (0, 0, {
                'search_id': self.id,
                'delivery_date': transfer.invoice_date,
                'invoice_id': transfer.id,
                'partner_id': transfer.partner_id.id,
                'delivery_address_id': transfer.partner_shipping_id.id,
                'transport_line_id': transfer.transport_line_id.id,
                'company_round_id': transfer.company_round_id.id,
                'sale_no': transfer.invoice_origin,
                'delivery_id': delivery_id.id if delivery_id else False,
                'sale_person': transfer.invoice_user_id.id,
                'status': transfer.state,
            })
            order_line.append(line)

        self.write({
            'invoice_line_ids': order_line
        })
    
    def clear_all_action(self):
        # self.scheduled_date_start = False
        # self.scheduled_date_end = False
        self.operation_type_id = False
        self.invoice_ids = False
        self.spe_invoice_ids = False
        self.partner_ids = False
        self.sale_order_ids = False
        self.delivery_order_ids = False
        self.transport_line_ids = False
        self.company_round_ids = False
        self.invoice_line_ids.unlink()

    def create_delivery_noted_action(self):
        if self.invoice_line_ids:
            return {
                'name': "Cofirm Delivery Noted",
                'view_mode': 'form',
                'res_model': 'wizard.confirm.delivery.noted',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_search_id': self.id,
                    'default_company_id': self.company_id.id,
                    'default_transport_line_id': self.invoice_line_ids[-1].transport_line_id.id,
                }
            }

    def select_all_line(self):
        for line in self.invoice_line_ids:
            line.selected = True

class SearchInvoiceLine(models.Model):
    _name = "search.invoice.line"
    _description = "search invoice line"

    search_id = fields.Many2one("resupply.transfer.branch.summary")
    delivery_date = fields.Date("Delivery Date")
    name = fields.Char(related='invoice_id.name', string="Invoice")
    partner_id = fields.Many2one('res.partner', string="Customer" )
    delivery_address_id = fields.Many2one('res.partner', string="Delivery Address")
    transport_line_id = fields.Many2one('delivery.round', string="สายส่ง TRL")
    company_round_id = fields.Many2one('company.delivery.round', string="Mode of delivery")
    invoice_id = fields.Many2one('account.move', string="Invoice",
        domain=[
            ('move_type', '=', 'out_invoice'),
        ])
    sale_no = fields.Char(string="SO No.")
    delivery_id = fields.Many2one('stock.picking', string="Delivery No." )
    sale_person = fields.Many2one('res.users', string="Sale Person" )
    status = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string="Status")
    
    delivery_date = fields.Date("Delivery Date")
    selected = fields.Boolean(string = "Selected")


class SearchBranchSummaryLine(models.Model):
    _name = "search.branch.summary.line"
    _description = "search branch summary line"

    search_id = fields.Many2one("resupply.transfer.branch.summary")
    
    product_id = fields.Many2one('product.product', string='Product')
    so_id = fields.Many2one('sale.order', string='SO No.')
    so_no = fields.Char(string='SO No.')
    # invoice_no = fields.Many2many(related='so_id.invoice_ids',string='Invoice')
    invoice_no = fields.Char(string='Invoice')
    name = fields.Char(related='product_id.name', string="Product")
    # branch_id = fields.Many2one('res.branch',string="Branch")
    # source_location = fields.Many2one('stock.location',string="Source Location")
    width = fields.Float( string='Width',digits=(16,2))
    height = fields.Float( string='Height',digits=(16,2))
    qty_available = fields.Float(related='product_id.qty_available', string='On Hand',digits=(16,2))
    qty_demand = fields.Float(string="Demand",digits=(16,2), readonly=True)
    qty_reserved = fields.Float(string="Reserved",digits=(16,2))
    uom_id = fields.Many2one("uom.uom", related='product_id.uom_id',  string="Unit of Measure")

