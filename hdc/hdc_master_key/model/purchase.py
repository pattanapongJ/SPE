from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.float_utils import float_compare, float_round
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseOrderTypeInherit(models.Model):
    _inherit = 'purchase.order.type'
    
    is_master_key_type = fields.Boolean(string='Is Master Key')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_master_key = fields.Boolean(string='Is Master Key',copy=False)
    count_so_purchase_master_key = fields.Integer(string='Purchase Master Key Count', compute='_compute_so_purchase_master_key_count')
    
    resupply_master_key_picking_id = fields.Many2one('stock.picking', string="Resupply Picking",copy=False)
    receipt_master_key_subcontract_id = fields.Many2one('stock.picking', string="Receipt MTK Subcontractor",copy=False)
    show_picking_button = fields.Boolean(compute='_compute_picking', string='Show Picking Button', copy=False, store=True)
    
    def action_edit_price(self):
        self.ensure_one()
        return {
                "name": "Change Price",
                "type": "ir.actions.act_window",
                "res_model": "wizard.purchase.mtk",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_purchase_id": self.id},
            }
    
    def _compute_so_purchase_master_key_count(self):
        for sale in self:
            po_ids = self.env['sale.order'].search([('name', '=', self.origin), ('is_master_key', '=', True)])
            list_po_ids = list(set(po_ids.ids))
            sale.count_so_purchase_master_key = len(list_po_ids)
    
    def action_so_view_purchase_master_key(self):
        po_ids = self.env['sale.order'].search([('name', '=', self.origin), ('is_master_key', '=', True)])
        res_id = list(set(po_ids.ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Purchase MTK', 'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action
    

    def action_view_resupply_picking(self):
        self.ensure_one()
        if not self.resupply_master_key_picking_id:
            raise UserError(_("ยังไม่มี Resupply Picking"))
        return {
            'name': _('Resupply Picking'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.resupply_master_key_picking_id.id,
        }

    def action_view_receipt_subcontract(self):
        self.ensure_one()
        if not self.receipt_master_key_subcontract_id:
            raise UserError(_("ยังไม่มี Receipt MTK Subcontractor"))
        return {
            'name': _('Receipt MTK Subcontractor'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.receipt_master_key_subcontract_id.id,
        }
    
    @api.depends('order_line.move_ids.picking_id')
    def _compute_picking(self):
        for order in self:
            if order.is_master_key:
                pickings = order.order_line.mapped('move_ids.picking_id')
                order.picking_ids = pickings
                order.picking_count = len(pickings)
                order.show_picking_button = False
                # return
            else:
                pickings = order.order_line.mapped('move_ids.picking_id')
                order.picking_ids = pickings
                order.picking_count = len(pickings)
                order.show_picking_button = bool(order.picking_ids)
                # result = super(PurchaseOrder, self)._compute_picking()
                # return result

    def _create_picking(self):
        StockPicking = self.env['stock.picking']        
        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):            
            if any(
                product.type == 'service' and product.is_master_key_service
                for product in order.order_line.product_id
            ):                
                order = order.with_company(order.company_id)                
                # pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))                
                if not order.resupply_master_key_picking_id:
                    res = order._prepare_mtk_picking(self.picking_type_id)
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                    if picking:
                        moves = order.order_line._create_stock_moves(picking)
                        moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                        seq = 0
                        for move in sorted(moves, key=lambda move: move.date):
                            seq += 5
                            move.sequence = seq                
                        moves._action_assign()                
                        picking.message_post_with_view(
                            'mail.message_origin_link',
                            values={'self': picking, 'origin': order},
                            subtype_id=self.env.ref('mail.mt_note').id
                        )

                        order.write({'resupply_master_key_picking_id': picking.id})
                
                if not order.receipt_master_key_subcontract_id:
                    res = order._prepare_mtk_picking(self.picking_type_id.receipt_master_key_subcontract_id)
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                    if picking:
                        moves = order.order_line._create_stock_moves(picking)
                        moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                        seq = 0
                        for move in sorted(moves, key=lambda move: move.date):
                            seq += 5
                            move.sequence = seq                
                        moves._action_assign()                
                        picking.message_post_with_view(
                            'mail.message_origin_link',
                            values={'self': picking, 'origin': order},
                            subtype_id=self.env.ref('mail.mt_note').id
                        )
                        
                        order.write({'receipt_master_key_subcontract_id': picking.id})

            else:
                super(PurchaseOrder, self)._create_picking()
        
        return True
    

    def _prepare_mtk_picking(self, picking_type):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id or False,
            })
        if not picking_type.id:
            raise UserError(_("olease Select Operation Type"))
        return {
            'purchase_id': self.id,
            'picking_type_id': picking_type.id,
            'partner_id': self.partner_id.id or False,
            'user_id': False,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'location_id': picking_type.default_location_src_id.id,
            'company_id': self.company_id.id,
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        vals = super()._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        vals['description_picking'] = self.name
        
        pt = picking.picking_type_id if picking else False
        if pt:
            if pt.default_location_src_id:
                vals['location_id'] = pt.default_location_src_id.id
            if pt.default_location_dest_id:
                vals['location_dest_id'] = pt.default_location_dest_id.id

        if self.product_id.type == 'service' and self.product_id.is_master_key_service:
            bom = self.env['mrp.bom'].search([('master_key_service_id', '=', self.product_id.id)], limit=1)
            if bom:
                sale_id = self.env['sale.order'].search([
                    ('purchase_master_key_id', '=', self.order_id.id),
                    ('is_master_key', '=', True)
                ], limit=1)
                dummy = sale_id.receipt_master_key_id.move_ids_without_package.filtered(
                    lambda l: l.product_id.is_master_key_dummy
                )
                if dummy:
                    product = sale_id.receipt_master_key_id.move_ids_without_package[0]
                    vals['description_picking'] = product.description_picking
                else:
                    product = bom.product_tmpl_id.product_variant_id
                    vals['description_picking'] = product._get_description(self.order_id.picking_type_id)

        return vals



    def _prepare_master_key_moves(self, picking, master_key_products):
        """Prepare stock moves for master key products in sale order lines, using SO data."""
        res_master_key = []
        for master_line in master_key_products:
            mk_product_id = master_line.product_id
            if mk_product_id.type in ['product', 'consu']:
                price_unit = master_line.price_unit
                qty = master_line.product_uom_qty
                product_uom = master_line.product_uom
                move_vals = self._prepare_stock_move_vals(picking, price_unit, qty, product_uom)
                move_vals['product_id'] = mk_product_id.id
                res_master_key.append(move_vals)
        return res_master_key

    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []

        # ตรวจสอบเงื่อนไขสำหรับ Master Key Service
        new_product_id = self.product_id  # เก็บค่าต้นฉบับของ Product ไว้
        if self.product_id.type == 'service' and self.product_id.is_master_key_service:            
            bom = self.env['mrp.bom'].search([('master_key_service_id', '=', self.product_id.id)], limit=1)
            sale_id = self.env['sale.order'].search([('purchase_master_key_id', '=', self.order_id.id), ('is_master_key', '=', True)], limit=1)
            dummy = sale_id.receipt_master_key_id.move_ids_without_package.filtered(lambda l: l.product_id.is_master_key_dummy)
            if bom:
                if dummy:
                    new_product_id = sale_id.receipt_master_key_id.move_ids_without_package[0].product_id
                else:
                    new_product_id = bom.product_tmpl_id.product_variant_id
            if sale_id:
                master_key_products = sale_id.order_line.filtered(lambda l: l.product_id.is_master_key_product)
                if master_key_products:
                    res_master_key = self._prepare_master_key_moves(picking, master_key_products)
                    res.extend(res_master_key)

            if new_product_id.type not in ['product', 'consu']:
                return res

            price_unit = self._get_stock_move_price_unit()
            qty = self._get_qty_procurement()

            move_dests = self.move_dest_ids
            if not move_dests:
                move_dests = self.move_ids.move_dest_ids.filtered(
                    lambda m: m.state != 'cancel' and not m.location_dest_id.usage == 'supplier'
                )

            if not move_dests:
                qty_to_attach = 0
                qty_to_push = self.product_qty - qty
            else:
                move_dests_initial_demand = new_product_id.uom_id._compute_quantity(
                    sum(move_dests.filtered(lambda m: m.state != 'cancel' and not m.location_dest_id.usage == 'supplier').mapped('product_qty')),
                    self.product_uom, rounding_method='HALF-UP'
                )
                qty_to_attach = min(self.product_qty, move_dests_initial_demand) - qty
                qty_to_push = self.product_qty - move_dests_initial_demand

            if float_compare(qty_to_attach, 0.0, precision_rounding=self.product_uom.rounding) > 0:
                product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(qty_to_attach, new_product_id.uom_id)
                move_vals = self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
                move_vals['product_id'] = new_product_id.id  # ใช้ product ใหม่ใน move
                res.append(move_vals)

            if float_compare(qty_to_push, 0.0, precision_rounding=self.product_uom.rounding) > 0:
                product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(qty_to_push, new_product_id.uom_id)
                extra_move_vals = self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
                extra_move_vals['product_id'] = new_product_id.id  # ใช้ product ใหม่ใน move
                extra_move_vals['move_dest_ids'] = False  # don't attach
                res.append(extra_move_vals)

            return res

        else:
            return super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
