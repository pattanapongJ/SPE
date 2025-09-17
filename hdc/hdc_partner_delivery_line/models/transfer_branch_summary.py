# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta

class ReSupplyTransferBranchSummary(models.Model):
    _inherit = "resupply.transfer.branch.summary"

    name = fields.Char(string="Generate Delivery Lists", readonly=True, default='Generate Delivery Lists')
    transport_line_id = fields.Many2many('delivery.round', domain=[('status_active', '=', True)])
    summary_delivery_ids = fields.One2many('search.branch.summary.delivery', 'search_id', string="Delivery Lines")

    def search_action(self):
        domain_search = []
        for rec in self:
            if rec.scheduled_date_start :
                if rec.scheduled_date_end and rec.scheduled_date_end < rec.scheduled_date_start:
                    raise UserError(_("The end date cannot be less than the start date."))
                datetime_start = (rec.scheduled_date_start - relativedelta(days=1)).strftime("%Y-%m-%d 17:00:00")
                domain_search += [('scheduled_date', '>=', datetime_start)]
            if rec.scheduled_date_end :
                datetime_end = (rec.scheduled_date_end).strftime("%Y-%m-%d 16:59:59")
                domain_search += [('scheduled_date', '<=', datetime_end)]
            if rec.operation_type_id :
                domain_search += [('picking_type_id', '=', datetime_end)]
            if rec.transport_line_id :
                domain_search += [('partner_id.delivery_line', 'in', rec.transport_line_id.ids)]
            
            operation_type_setting_id = self.env['stock.picking.type'].search([('code', '=', "outgoing")],limit=1)
            transfer_search_config = rec.env['stock.picking'].search(domain_search + [
                ('picking_type_id', '=', operation_type_setting_id.id),
            ])
            rec.summary_line_ids.unlink()
            rec.summary_delivery_ids.unlink()
            order_product_line = []
            order_delivery_line = []
            for transfer in transfer_search_config:
                if transfer.state == 'assigned' and not transfer.delivery_list_id:
                    active_picking = False
                    for move_line in transfer.move_ids_without_package:
                        so_id = rec.env['sale.order'].search([('name','=', move_line.origin)],limit=1)
                        if so_id:
                            for invoice_id in so_id.invoice_ids :
                                if invoice_id.state != 'cancel':
                                    active_picking = True
                                    invoice_no = invoice_id
                                    line = (0, 0, {
                                        'search_id': rec.id,
                                        'product_id': move_line.product_id.id,
                                        'move_id': move_line.id,
                                        'picking_id': transfer.id,
                                        'qty_available': move_line.product_id.qty_available,
                                        'qty_demand': move_line.product_uom_qty,
                                        'qty_reserved': move_line.reserved_availability,
                                        'uom_id': move_line.product_id.uom_id.id,
                                        'so_id': so_id.id,
                                        'so_no': move_line.origin,
                                        'invoice_id': invoice_no.id
                                        })
                                    order_product_line.append(line)
                    if active_picking:
                        line_delivery = (0, 0, {
                            'search_id': rec.id,
                            'picking_id': transfer.id,
                            })
                        order_delivery_line.append(line_delivery)
            rec.write({
                'summary_line_ids': order_product_line,
                'summary_delivery_ids': order_delivery_line
            })
    
    def clear_all_action(self):
        # self.branch_ids = False
        self.transport_line_id = False
        self.scheduled_date_start = False
        self.scheduled_date_end = False
        self.operation_type_id = False
        # self.total_weight = False
        self.summary_line_ids.unlink()
        self.summary_delivery_ids.unlink()

    def create_delivery_noted_action(self):
        if self.summary_line_ids:
            return {
                    'name': "Cofirm Delivery Noted",
                    'view_mode': 'form',
                    'res_model': 'wizard.confirm.delivery.noted',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {
                        'default_search_id': self.id,
                        # 'default_total_weight': self.total_weight
                    }
                }
   
    
class SearchBranchSummaryLine(models.Model):
    _inherit = "search.branch.summary.line"

    so_id = fields.Many2one('sale.order', string='SO No.', readonly=True)
    so_no = fields.Char(string='SO No.', readonly=True)
    invoice_no = fields.Char(string='Invoice', readonly=True)
    width = fields.Float( string='Width',digits=(16,2), readonly=True)
    height = fields.Float( string='Height',digits=(16,2), readonly=True)
    qty_demand = fields.Float(string="Demand",digits=(16,2), readonly=True)
    qty_reserved = fields.Float(string="Reserved",digits=(16,2), readonly=True)

    picking_id = fields.Many2one('stock.picking', string='Picking Delivery')
    invoice_id = fields.Many2one( 'account.move',string='Invoice', readonly=True)
    move_id = fields.Many2one("stock.move")
    state = fields.Selection(related='move_id.state', string="Status")
    delivery_address = fields.Many2one(related='picking_id.partner_id')
    delivery_line = fields.Many2one(related='picking_id.partner_id.delivery_line', readonly=False)
    
    def delete_related_records(self):
        for rec in self:
            search_line = self.env['search.branch.summary.line'].search([('id','!=', self.id),('picking_id','=',rec.picking_id.id),('search_id','=',rec.search_id.id)])
            if not search_line:
                related_records = self.env['search.branch.summary.delivery'].search([('picking_id','=',rec.picking_id.id),('search_id','=',rec.search_id.id)])
                if related_records:
                    related_records.unlink()
            self.unlink()
    
   
class SearchBranchSummaryDelivery(models.Model):
    _name = "search.branch.summary.delivery"
    _description = "search branch summary delivery"

    search_id = fields.Many2one("resupply.transfer.branch.summary")
    
    picking_id = fields.Many2one('stock.picking', string='Picking Delivery')
    name = fields.Char(related='picking_id.name', string="Picking Delivery")
    scheduled_date = fields.Datetime(related='picking_id.scheduled_date', string="Picking Delivery")
    location_id = fields.Many2one(related='picking_id.location_id', string="Source Location")
    backorder_id = fields.Many2one(related='picking_id.backorder_id', string="Back Order of")
    origin = fields.Char(related='picking_id.origin', string="Souce Document")
    state = fields.Selection(related='picking_id.state', string="Status")

    def delete_related_records(self):
        for rec in self:
            related_records = self.env['search.branch.summary.line'].search([('so_no','=',rec.origin),('search_id','=',rec.search_id.id)])
            if related_records:
                related_records.unlink()
            self.unlink()