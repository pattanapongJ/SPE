# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class WizardCancelSoLine(models.TransientModel):
    _name = "wizard.cancel.so.line"
    _description = "Wizard Cancel So By Line"

    line_ids = fields.One2many('wizard.cancel.so.line.line', 'wizard_cancel', string = 'Cancel Order Line Item')

    def cancel_line(self):
        for line in self.line_ids:
            cancel_qty = abs(line.cancel_qty)
            cancel_qty_all = abs(line.cancel_qty)
            stock_picking_id = line.move_id.picking_id
            if cancel_qty <=0:
                raise UserError(_("กรุณาใส่จำนวนที่จะยกเลิก"))
            if line.move_id.product_uom_qty < cancel_qty:
                raise UserError(_("จำนวนของที่จะยกเลิกมามากกว่าจำนวนที่รอจัดส่ง"
                                    "\nกรุณาตรวจสอบจำนวนที่จะยกเลิกอีกครั้ง"))
            picking_line_ids = self.env['picking.lists.line'].search(
                    [('order_line', '=', line.order_line.id),
                     ('picking_lists.state', 'in', ["draft","waiting_pick"]),
                     ('state_cancel', '=', False),],order='id asc')
            picking_ids = picking_line_ids.mapped('picking_lists')
            for pk_list in picking_line_ids:
                if cancel_qty <=0 :
                    break
                if pk_list.amount_arranged <= cancel_qty:
                    cancel_qty -= pk_list.amount_arranged
                    pk_list.state_cancel = True
                else:
                    cancel_qty = 0
                    pk_list.state_cancel = True
                pk_list.amount_arranged = 0.0
            for picking in picking_ids:
                if all(line.state_cancel for line in picking.list_line_ids):
                    picking.action_cancel()

            line.order_line.cancel_qty += cancel_qty_all
            line.order_line.canceled_by = self.env.user  
            line.order_line.canceled_at = fields.Datetime.now()
            stock_picking_id.do_unreserve()
            line.move_id.product_uom_qty -= cancel_qty_all
            line.move_id.qty_counted -= cancel_qty_all
            line.move_id.cancel_qty += cancel_qty_all
            stock_picking_id.action_assign()
            cancel_stock_picking = False
            for m_line in stock_picking_id:
                if all(m.product_uom_qty == 0 for m in m_line.move_ids_without_package):
                    cancel_stock_picking = True
            if cancel_stock_picking:
                for m_line_id in stock_picking_id:
                    cancel_pick = m_line_id.action_cancel()
                    # for line_state in m_line_id.move_ids_without_package:
                    #     a = line_state._action_cancel()
            # c้เรื่อง เคส ยกเลิกใน delivery
            # line.move_id.picking_lists.do_unreserve()
            # line.move_id.picking_lists.action_available()
        line.order_line.order_id.message_post(
        body=_(
                "Line Canceled: Product <b>%s</b>, Qty: <b>%s</b> %s by <b>%s</b>"
            ) % (
                line.product_id.display_name,
                line.cancel_qty,
                line.uom_id.name or '',
                self.env.user.name
            ),
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )



class WizardCancelSoLineLine(models.TransientModel):
    _name = "wizard.cancel.so.line.line"
    _description = "Wizard Cancel So Line"

    wizard_cancel = fields.Many2one('wizard.cancel.so.line', string="Wizard Cancel So By Line")
    order_line = fields.Many2one("sale.order.line", string = "Sale Order")
    move_id = fields.Many2one('stock.move', string = "Stock Moves", copy = False)

    product_id = fields.Many2one('product.product', string = 'Product', readonly = True)
    categ_id = fields.Many2one(related = "product_id.categ_id", string='Product Category', readonly = True)
    location_id = fields.Many2one(related = "move_id.location_id", string = 'Source Location', required = True, readonly = True)
    pick_location_id = fields.Many2one('stock.location',readonly = True, string = 'Location')
    demand_qty = fields.Float(string="Demand", digits = 'Product Unit of Measure', readonly = True,compute = "_compute_qty_ava",)
    virtual_available = fields.Float("Available Location", compute="_compute_qty_ava", digits = 'Product Unit of Measure', readonly = True)
    picking_draft = fields.Float("Picking Draft", compute = "_compute_qty_ava", digits = 'Product Unit of Measure', readonly = True)
    picked_qty = fields.Float("Picked QTY", compute = "_compute_qty_ava", digits = 'Product Unit of Measure', readonly = True)
    cancel_qty = fields.Float("Cancel QTY", digits = 'Product Unit of Measure')
    canceled_qty = fields.Float("Canceled QTY",related='order_line.cancel_qty', digits = 'Product Unit of Measure')
    uom_id = fields.Many2one("uom.uom", string = "UOM", readonly = True)

    def _compute_qty_ava(self):
        for rec in self:
            PickingListLine = rec.env['picking.lists.line']
            # First Define
            rec.demand_qty = rec.order_line.product_uom_qty
            product_bom = rec.env['mrp.bom'].search([('product_tmpl_id', '=', rec.order_line.product_id.product_tmpl_id.id),('type', '=', 'normal')], limit=1)
            if not rec.order_line.order_id.type_id.modern_trade and rec.order_line.product_id.route_ids.filtered(lambda l: l.name == "Manufacture") and product_bom:
                for line_bom in product_bom.bom_line_ids:
                    if rec.product_id == line_bom.product_id:
                        rec.demand_qty = line_bom.product_qty * rec.order_line.product_uom_qty
            else:
                # ถ้าไม่มี BoM ใช้จำนวนที่สั่งของสินค้าหลักโดยตรง
                rec.demand_qty = rec.order_line.product_uom_qty
            quant_id = rec.env['stock.quant'].search([('product_id','=', rec.product_id.id),('location_id','=',rec.pick_location_id.id)])
            if quant_id:
                if len(quant_id) == 1:
                    rec.virtual_available = quant_id.available_quantity
                else:
                    virtual_available = 0
                    for quant in quant_id:
                        virtual_available += quant.available_quantity
                    rec.virtual_available = virtual_available
            else:
                rec.virtual_available = 0
            picking_id_all = PickingListLine.search([('product_id', '=', rec.product_id.id), ('sale_id', '=', rec.order_line.order_id.id),('picking_lists.type_pl','!=','rma')])
            picking_id_done = picking_id_all.filtered(lambda l: l.state == 'done')
            rec.picked_qty = sum(picking_id_done.mapped('qty_done'))
            picking_draft = picking_id_all.filtered(lambda l: l.state == 'draft')
            rec.picking_draft = sum(picking_draft.mapped('qty'))

