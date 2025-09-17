from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from odoo.exceptions import Warning

class WizardMrProductReceive(models.TransientModel):
    _name = "wizard.mr.product.receive"
    _description = "Wizard Mr Product Receive"

    mr_id = fields.Many2one('mrp.mr', string='MR ID', ondelete='cascade')
    product_line_ids = fields.One2many('wizard.mr.product.receive.line', 'wiz_id')
    selected = fields.Boolean(string="Select")

    @api.onchange('selected')
    def selected_change(self):
        for line in self.product_line_ids:
            if self.selected:
                line.selected = True
            else:
                line.selected = False

    def action_receive_product(self):
        product_list = []

        new_picking = self.env['stock.picking'].create({
            'partner_id': self.mr_id.partner_id.id,
            'picking_type_id': self.mr_id.request_type.receipt_picking_type_id.id,
            'state': 'draft',
            'mr_id': self.mr_id.id,
            'origin': self.mr_id.name,
            'location_id': self.mr_id.request_type.receipt_picking_type_id.default_location_src_id.id,
            'location_dest_id': self.mr_id.request_type.receipt_picking_type_id.default_location_dest_id.id,
            })
        for line in self.product_line_ids:  # วนลูปสำหรับสินค้าแต่ละรายการ
            if line.selected:
                move = self.env['stock.move'].create({
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.receive_qty,  # จำนวนสินค้า
                    'product_uom': line.product_uom.id,
                    'location_id': self.mr_id.request_type.receipt_picking_type_id.default_location_src_id.id,
                    'location_dest_id': self.mr_id.request_type.receipt_picking_type_id.default_location_dest_id.id,
                    'picking_id': new_picking.id,  # ระบุใบ Picking ที่เพิ่งสร้าง
                    'origin': self.mr_id.name,
                    'state': 'draft',
                })

class WizardMrProductReceiveLine(models.TransientModel):
    _name = "wizard.mr.product.receive.line"
    _description = "Wizard Mr Product Receive Line"

    wiz_id = fields.Many2one("wizard.mr.product.receive")
    selected = fields.Boolean(string="Select")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    name = fields.Text(string="Description")
    demand_qty_modify = fields.Float("Demand Modify",)
    remain_receive_qty = fields.Float("Remain Receive",)
    receive_qty = fields.Float(string="Receive")
    product_uom = fields.Many2one(comodel_name="uom.uom", string="UOM",domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    @api.onchange('receive_qty')
    def receive_qty_change(self):
        if self.receive_qty > self.remain_receive_qty:
            raise Warning(_('กรุณาตรวจสอบจำนวนรับสินค้า Modify อีกครั้ง'))
