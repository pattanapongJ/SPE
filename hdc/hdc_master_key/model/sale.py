from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
import re

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_master_key = fields.Boolean(
        string='Is MTK', 
        compute='_compute_master_key', 
        store=True, 
    )

    receipt_master_key_id = fields.Many2one('stock.picking', string='Receipt MTK',copy=False)
    transfer_master_key_id = fields.Many2one('stock.picking', string='Transfer MTK',copy=False)
    internal_transfer_master_key_id = fields.Many2one('stock.picking', string='Internal Transfer MTK', copy=False)
    purchase_master_key_id = fields.Many2one('purchase.order', string='Purchase MTK',copy=False)

    internal_mtk_type_id = fields.Many2one(
        'stock.picking.type', 
        string='Internal Transfer MTK',
        domain="[('is_internal_transfer_master_key', '=', True), ('company_id', '=', company_id)]", copy=False
        
    )

    count_receipt_master_key = fields.Integer(string='Receipt MTK Count', compute='_compute_master_key_counts')
    count_purchase_master_key = fields.Integer(string='Purchase MTK Count', compute='_compute_master_key_counts')
    count_transfer_master_key = fields.Integer(string='Transfer MTK Count', compute='_compute_master_key_counts')
    count_internal_transfer_master_key = fields.Integer(string='Internal Transfer MTK Count', compute='_compute_master_key_counts')

    def _compute_master_key_counts(self):
        for sale in self:
            company_id = self.env.context.get('company_id') or self.env.company.id
            picking_type_receipt = self.env['stock.picking.type'].with_company(company_id).search([
                ('is_master_key', '=', True),
                ('company_id', '=', company_id),
                ], limit=1)
            receipt_pickings = self.env['stock.picking'].search([
                ('origin', '=', sale.name), 
                ('picking_type_id', '=', picking_type_receipt.id)
            ])
            sale.count_receipt_master_key = len(set(receipt_pickings.ids))

            purchase_orders = self.env['purchase.order'].search([
                ('origin', '=', sale.name), 
                ('is_master_key', '=', True)
            ])
            sale.count_purchase_master_key = len(set(purchase_orders.ids))

            picking_type_transfer = self.env['stock.picking.type'].with_company(company_id).search([
                ('is_transfer_master_key', '=', True),
                ('company_id', '=', company_id),
                ], limit=1)
            transfer_pickings = self.env['stock.picking'].search([
                ('origin', '=', sale.name), 
                ('picking_type_id', '=', picking_type_transfer.id)
            ])
            sale.count_transfer_master_key = len(set(transfer_pickings.ids))

            picking_type_internal_transfer = self.env['stock.picking.type'].with_company(company_id).search([
                ('is_internal_transfer_master_key', '=', True),
                ('company_id', '=', company_id),
                ], limit=1)
            internal_transfer_pickings = self.env['stock.picking'].search([
                ('origin', '=', sale.name), 
                ('picking_type_id', '=', picking_type_internal_transfer.id)
            ])
            sale.count_internal_transfer_master_key = len(set(internal_transfer_pickings.ids))

    def action_view_transfer_master_key(self):
        company_id = self.env.context.get('company_id') or self.env.company.id
        picking_type = self.env['stock.picking.type'].with_company(company_id).search([
            ('is_transfer_master_key', '=', True),
            ('company_id', '=', company_id),
            ], limit=1)
        picking_ids = self.env['stock.picking'].search([('origin', '=', self.name), ('picking_type_id', '=', picking_type.id)])
        res_id = list(set(picking_ids.ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Transfer MTK', 'type': 'ir.actions.act_window', 'res_model': 'stock.picking', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action
    
    def action_view_internal_transfer_master_key(self):
        company_id = self.env.context.get('company_id') or self.env.company.id
        picking_type = self.env['stock.picking.type'].with_company(company_id).search([
            ('is_internal_transfer_master_key', '=', True),
            ('company_id', '=', company_id),
            ], limit=1)
        picking_ids = self.env['stock.picking'].search([('origin', '=', self.name), ('picking_type_id', '=', picking_type.id)])
        res_id = list(set(picking_ids.ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Internal Transfer MTK', 'type': 'ir.actions.act_window', 'res_model': 'stock.picking', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action
    
    def action_view_receipt_master_key(self):
        company_id = self.env.context.get('company_id') or self.env.company.id
        picking_type = self.env['stock.picking.type'].with_company(company_id).search([
            ('is_master_key', '=', True),
            ('company_id', '=', company_id),
            ], limit=1)
        picking_ids = self.env['stock.picking'].search([('origin', '=', self.name), ('picking_type_id', '=', picking_type.id)])
        res_id = list(set(picking_ids.ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Receipt MTK', 'type': 'ir.actions.act_window', 'res_model': 'stock.picking', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action
    
    def action_view_purchase_master_key(self):
        po_ids = self.env['purchase.order'].search([('origin', '=', self.name), ('is_master_key', '=', True)])
        res_id = list(set(po_ids.ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Purchase MTK', 'type': 'ir.actions.act_window', 'res_model': 'purchase.order', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action

    @api.depends('order_line.product_id.is_master_key_product', 
                'order_line.product_id.is_master_key_service',
                'order_line','state')
    def _compute_master_key(self):
        for order in self:
            if not order.order_line:
                order.is_master_key = False
                continue
                
            all_master_key = all(
                line.product_id and 
                (line.product_id.is_master_key_product or 
                 line.product_id.is_master_key_service)
                for line in order.order_line
            )
            order.is_master_key = all_master_key

    @api.model
    def _default_picking_type(self):
        company_id = self.env.context.get('company_id') or self.env.company.id
        return self._get_picking_type(company_id)

    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].with_company(company_id).search([
            ('is_master_key', '=', True),
            ('code', '=', 'incoming'),
            '|',
            ('warehouse_id.company_id', '=', company_id),
            ('warehouse_id', '=', False)
        ])
        
        return picking_type[:1]
    
    def _get_invoice_status(self):
        super(SaleOrder, self)._get_invoice_status()
        for order in self:            
            if order.is_master_key:
                master_key_lines = order.order_line.filtered(lambda line: line.product_id.is_master_key_service 
                    and not line.is_downpayment and not line.display_type)
                if master_key_lines:
                    order.invoice_status = 'no'
                    for line in master_key_lines:
                        line.invoice_status = 'no'

    def action_create_receipt_master_key(self):
        for order in self:
            company_id = self.env.context.get('company_id') or self.env.company.id
            if order.receipt_master_key_id:
                raise UserError(
                            _(
                                "คุณเคยสร้างใบ MTK แล้ว"
                            )
                        )
        
            picking_type = self.env['stock.picking.type'].with_company(company_id).search([
                ('is_master_key', '=', True),
                ('company_id', '=', company_id),
                ], limit=1)
            if not picking_type:
                raise UserError(_("No MTK Picking Type Found."))

            picking_vals = {
                'picking_type_id': picking_type.id,
                'sale_id': order.id,
                'partner_id': order.partner_id.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'origin': order.name,
                'company_id': order.company_id.id,
            }

            picking = self.env['stock.picking'].create(picking_vals)
            if not self.receipt_master_key_id:
                self.receipt_master_key_id = picking.id
            
            dummy_product = self.env['product.product'].search([('product_tmpl_id.is_master_key_dummy', '=', True)], limit=1)
            if len(order.order_line) == 1 and order.order_line[0].product_id.is_master_key_service and dummy_product:
                for line in order.order_line.filtered(lambda l: l.product_id.is_master_key_service):
                    move_vals = {
                        'name': "",
                        'product_id': dummy_product.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'picking_id': picking.id,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': picking_type.default_location_dest_id.id,
                        'company_id': order.company_id.id,
                    }
                    move = self.env['stock.move'].create(move_vals)
            else:
                for line in order.order_line.filtered(lambda l: l.product_id.type != 'service'):
                    move_vals = {
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'picking_id': picking.id,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': picking_type.default_location_dest_id.id,
                        'company_id': order.company_id.id,
                    }
                    move = self.env['stock.move'].create(move_vals)
        return {
            'name': _('Stock Picking'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'type': 'ir.actions.act_window',
        }
    
    def action_create_purchase_master_key(self):
        self.ensure_one()
        for sale in self:
            if sale.purchase_master_key_id:
                raise UserError(
                            _(
                                "คุณเคยสร้างใบ MTK แล้ว"
                            )
                        )
            return {
                    "name": "Create Purchase MTK",
                    "type": "ir.actions.act_window",
                    "res_model": "wizard.create.purchase.mtk",
                    "view_mode": 'form',
                    'target': 'new',
                    "context": {"default_sale_id": sale.id},
                }
    
    # def action_create_purchase_master_key(self):
    #     purchase_order_obj = self.env['purchase.order']
    #     purchase_line_obj = self.env['purchase.order.line']
        
    #     for sale in self:
    #         if sale.purchase_master_key_id:
    #             raise UserError(
    #                         _(
    #                             "คุณเคยสร้างใบ MTK แล้ว"
    #                         )
    #                     )
            
    #         purchase_order = purchase_order_obj.create({
    #             'partner_id': sale.partner_id.id,
    #             'is_master_key': sale.is_master_key,
    #             'origin': sale.name,
    #             'picking_type_id': sale._default_picking_type().id if sale._default_picking_type() else False,
    #             'order_line': [],
    #         })

    #         if not self.purchase_master_key_id:
    #             self.purchase_master_key_id = purchase_order.id
                
    #         for line in sale.order_line:
    #             if line.product_id.type == 'service' and line.product_id.is_master_key_service:
    #                 purchase_line_obj.create({
    #                     'order_id': purchase_order.id,
    #                     'product_id': line.product_id.id,
    #                     'name': line.name,
    #                     'product_uom': line.product_uom.id,
    #                     'product_qty': line.product_uom_qty,
    #                     'price_unit': line.price_unit,
    #                 })

    #         if not purchase_order.order_type:
    #             purchase_order.order_type = purchase_order._default_order_type()

    #         purchase_order.button_confirm_inter_com()
    #         purchase_order.confirm_po()


    #     return {
    #         'name': _('Purchase Order'),
    #         'view_mode': 'form',
    #         'res_model': 'purchase.order',
    #         'res_id': purchase_order.id,
    #         'type': 'ir.actions.act_window',
    #     }

    def action_create_transfer_master_key(self):
        for order in self:
            company_id = self.env.context.get('company_id') or self.env.company.id
            if order.transfer_master_key_id:
                raise UserError(
                            _(
                                "คุณเคยสร้างใบ MTK แล้ว"
                            )
                        )
            picking_type = self.env['stock.picking.type'].with_company(company_id).search([
                ('is_transfer_master_key', '=', True),
                ('company_id', '=', company_id),
                ], limit=1)
            if not picking_type:
                raise UserError(_("No MTK Picking Type Found."))

            picking_vals = {
                'picking_type_id': picking_type.id,
                'sale_id': order.id,
                'partner_id': order.partner_id.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'origin': order.name,
                'company_id': order.company_id.id,
            }

            picking = self.env['stock.picking'].create(picking_vals)
            if not self.transfer_master_key_id:
                self.transfer_master_key_id = picking.id

            dummy = self.receipt_master_key_id.move_ids_without_package.filtered(lambda l: l.product_id.is_master_key_dummy)
            if dummy:
                for line in order.receipt_master_key_id.move_ids_without_package.filtered(lambda l: l.product_id.is_master_key_dummy):
                    move_vals = {
                        'name': line.name,
                        'description_picking': line.description_picking,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'picking_id': picking.id,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': picking_type.default_location_dest_id.id,
                        'company_id': order.company_id.id,
                    }
                    move = self.env['stock.move'].create(move_vals)
            else:
                for line in order.order_line.filtered(lambda l: l.product_id.type != 'service'):
                    move_vals = {
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'picking_id': picking.id,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': picking_type.default_location_dest_id.id,
                        'company_id': order.company_id.id,
                    }
                    move = self.env['stock.move'].create(move_vals)
        return {
            'name': _('Stock Picking'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'type': 'ir.actions.act_window',
        }

    def action_create_internal_transfer_master_key(self):
        for order in self:
            if not order.internal_mtk_type_id:
                raise UserError(
                            _(
                                "กรุณาระบุการโอนย้ายภายในมาสเตอร์คีย์"
                            )
                        )
        
            if order.internal_transfer_master_key_id:
                raise UserError(
                            _(
                                "คุณเคยสร้างใบ MTK แล้ว"
                            )
                        )
            
            picking_type = order.internal_mtk_type_id
            if not picking_type:
                raise UserError(_("No MTK Picking Type Found."))

            picking_vals = {
                'picking_type_id': picking_type.id,
                'sale_id': order.id,
                'partner_id': order.partner_id.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'origin': order.name,
                'company_id': order.company_id.id,
            }

            picking = self.env['stock.picking'].create(picking_vals)
            if not self.internal_transfer_master_key_id:
                self.internal_transfer_master_key_id = picking.id

            for line in order.order_line.filtered(lambda l: l.product_id.type != 'service'):
                move_vals = {
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'picking_id': picking.id,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                    'company_id': order.company_id.id,
                }
                move = self.env['stock.move'].create(move_vals)

        return {
            'name': _('Stock Picking'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'type': 'ir.actions.act_window',
        }