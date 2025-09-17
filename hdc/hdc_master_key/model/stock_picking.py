import logging

from datetime import timedelta

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
from dateutil.relativedelta import relativedelta

from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    is_master_key = fields.Boolean(string='Is Receipt MTK')
    is_transfer_master_key = fields.Boolean(string='Is Transfer MTK')
    is_internal_transfer_master_key = fields.Boolean(string='Is Internal Transfer MTK')

    is_master_key_resupply_subcontract = fields.Boolean(string='Resupply Subcontractor')
    receipt_master_key_subcontract_id = fields.Many2one('stock.picking.type', string='Receipt MTK Subcontractor')

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_master_key = fields.Boolean(related='picking_type_id.is_master_key', store=True)
    is_transfer_master_key = fields.Boolean(related='picking_type_id.is_transfer_master_key', store=True)
    is_internal_transfer_master_key = fields.Boolean(related='picking_type_id.is_internal_transfer_master_key', store=True)
    is_resupply_master_key = fields.Boolean(related='picking_type_id.is_master_key_resupply_subcontract', store=True)
    count_so_receipt_master_key = fields.Integer(string='Receipt Master Key Count', compute='_compute_master_key_count')
    count_so_transfer_master_key = fields.Integer(string='Transfer Master Key Count', compute='_compute_master_key_count')
    count_so_internal_transfer_master_key = fields.Integer(string='Internal Transfer Master Key Count', compute='_compute_master_key_count')

    count_po_resupply_master_key = fields.Integer(string='Purchase Resupply Master Key Count', compute='_compute_master_key_count')
    count_po_receipt_master_key = fields.Integer(string='Purchase Receipt Master Key Count', compute='_compute_master_key_count')

    def print_master_key(self):
        return self.env.ref('hdc_master_key.hdc_master_key_report').report_action(self.id)

    def _compute_master_key_count(self):
        for sale in self:
            so_ids1 = self.env['sale.order'].search([
                ('name', '=', self.origin), 
                ('is_master_key', '=', True), 
                ('receipt_master_key_id', '=', self.id),
                ('receipt_master_key_id.picking_type_id.is_master_key', '=', True)
            ])
            list_picking1 = list(set(so_ids1.ids))
            sale.count_so_receipt_master_key = len(list_picking1)

            so_ids2 = self.env['sale.order'].search([
                ('name', '=', self.origin), 
                ('is_master_key', '=', True), 
                ('transfer_master_key_id', '=', self.id),
                ('transfer_master_key_id.picking_type_id.is_transfer_master_key', '=', True)
            ])
            list_picking2 = list(set(so_ids2.ids))
            sale.count_so_transfer_master_key = len(list_picking2)

            so_ids3 = self.env['sale.order'].search([
                ('name', '=', self.origin), 
                ('is_master_key', '=', True), 
                ('internal_transfer_master_key_id', '=', self.id),
                ('internal_transfer_master_key_id.picking_type_id.is_internal_transfer_master_key', '=', True)
            ])
            list_picking3 = list(set(so_ids3.ids))
            sale.count_so_internal_transfer_master_key = len(list_picking3)

            po_ids = self.env['purchase.order'].search([
                ('name', '=', self.origin), 
                ('is_master_key', '=', True), 
                ('resupply_master_key_picking_id', '=', self.id),
                # ('is_resupply_master_key', '=', True)
            ])
            list_po_picking = list(set(po_ids.ids))
            sale.count_po_resupply_master_key = len(list_po_picking)

            po_ids1 = self.env['purchase.order'].search([
                ('name', '=', self.origin), 
                ('is_master_key', '=', True), 
                ('receipt_master_key_subcontract_id', '=', self.id),
            ])
            list_po1_picking = list(set(po_ids1.ids))
            sale.count_po_receipt_master_key = len(list_po1_picking)
    
    def action_view_so_receipt_master_key(self):
        so_ids = self.env['sale.order'].search([('name', '=', self.origin), ('is_master_key', '=', True), 
                                                     ('receipt_master_key_id', '=', self.id),
                                                     ('receipt_master_key_id.picking_type_id.is_master_key', '=', True)
                                                     ])
        res_id = list(set(so_ids.ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Receipt MTK', 'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action

    def action_view_so_transfer_master_key(self):
        so_ids = self.env['sale.order'].search([('name', '=', self.origin), ('is_master_key', '=', True), 
                                                     ('transfer_master_key_id', '=', self.id),
                                                     ('transfer_master_key_id.picking_type_id.is_transfer_master_key', '=', True)
                                                     ])
        res_id = list(set(so_ids.ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Transfer MTK', 'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action
    
    def action_view_so_internal_transfer_master_key(self):
        so_ids = self.env['sale.order'].search([('name', '=', self.origin), ('is_internal_transfer_master_key', '=', True), 
                                                     ('internal_transfer_master_key_id', '=', self.id),
                                                     ('internal_transfer_master_key_id.picking_type_id.is_internal_transfer_master_key', '=', True)
                                                     ])
        res_id = list(set(so_ids.ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Internal Transfer MTK', 'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action
    
    def action_view_po_receipt_master_key(self):
        po_ids = self.env['purchase.order'].search([('name', '=', self.origin), ('id', '=', self.purchase_id.id), 
                                                     ('receipt_master_key_subcontract_id', '=', self.id), ('is_master_key', '=', True),
                                                     ])
        res_id = list(set(po_ids.ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Purchase Receipt MTK', 'type': 'ir.actions.act_window', 'res_model': 'purchase.order', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action
    
    def action_view_po_resupply_master_key(self):
        po_ids = self.env['purchase.order'].search([('name', '=', self.origin), ('id', '=', self.purchase_id.id),
                                                     ('resupply_master_key_picking_id', '=', self.id), ('is_master_key', '=', True)
                                                     ])
        res_id = list(set(po_ids.ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Purchase Resupply MTK', 'type': 'ir.actions.act_window', 'res_model': 'purchase.order', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action