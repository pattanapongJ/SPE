from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError, ValidationError

class WizardSplitReceiptIN(models.TransientModel):
    _name = "wizard.split.receipt.in"
    _description = "Wizard Split Receipt IN"

    picking_id = fields.Many2one(comodel_name="stock.picking")
    company_id = fields.Many2one(related='picking_id.company_id', string="Company")
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Operation Type",
        required=True,
        domain=[('code', '=','incoming')]
    )
    warehouse_id = fields.Many2one("stock.warehouse", string = "Warehouse", readonly=True)
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', required=True)
    scheduled_date = fields.Datetime('Scheduled Date', default=fields.Datetime.now,)
    user_employee_id = fields.Many2one('hr.employee', string = 'Responsibles')
    product_line_ids = fields.One2many('wizard.split.receipt.in.line', 'wiz_id')
    
    location_id = fields.Many2one('stock.location', string='Source Location')
    product_ids = fields.Many2many(comodel_name="product.product",string="Product Receipts")
    update_product = fields.Boolean(string="Update Product")
    selected = fields.Boolean(string="Select All")
    currency_id = fields.Many2one('res.currency', string='Currency',)
    amount_untaxed = fields.Monetary(string='Untaxed')
    amount_tax = fields.Monetary(string='Vat')
    amount_total = fields.Monetary(string='Total')
    update_total = fields.Boolean(string="Update Total")

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        if self.picking_type_id.default_location_dest_id.id:
            self.location_dest_id = self.picking_type_id.default_location_dest_id.id
        self.warehouse_id = self.picking_type_id.id

    @api.onchange('location_dest_id')
    def _onchange_location_dest_id(self):
        for line in self.product_line_ids:
            line.location_dest_id = self.location_dest_id

    def action_create_receipt_in(self):
        if self.product_line_ids:
            order_line_ids = []
            for line in self.product_line_ids:
                if line.selected:
                    if line.receive_qty > 0:
                        line_data = (0, 0, {
                            'product_id': line.product_id.id,
                            'name': line.product_id.name,
                            'product_uom_qty': line.receive_qty,
                            'date': self.scheduled_date,
                            'location_id': line.location_id.id,
                            'location_dest_id': line.location_dest_id.id,
                            'product_uom': line.product_uom.id,
                            'purchase_line_id': line.move_id.purchase_line_id.id,
                            'price_unit': line.price_unit,
                        })
                        order_line_ids.append(line_data)
                        remain_product_uom_qty = line.move_id.product_uom_qty - line.receive_qty
                        po_remain = line.move_id.po_remain - line.po_receive_qty
                        line.move_id.po_qty_counted = po_remain
                        line.move_id.product_uom_qty = remain_product_uom_qty
                        line.move_id.qty_counted = remain_product_uom_qty
                    
            stock = self.env['stock.picking']
            stock_id = stock.create({
                'picking_origin_split_id': self.picking_id.id,
                'partner_id': self.picking_id.partner_id.id,
                'purchase_id': self.picking_id.purchase_id.id,
                'origin': self.picking_id.origin,
                'scheduled_date': self.scheduled_date,
                'move_ids_without_package': order_line_ids,
                'picking_type_id': self.picking_type_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'user_employee_id':self.user_employee_id.id,
            }).id
            action = {
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'res_id': stock_id,
                'target': 'self',
            }
            return action
    
    @api.onchange("update_product")
    def _onchange_update_product(self):
        if self.update_product == True:
            if self.product_ids:
                clear_list = []
                for line in self.product_line_ids:
                    if line.product_id.id not in self.product_ids.ids:
                        clear_list.append((3, line.id, 0))
                if clear_list:
                    self.product_line_ids = clear_list
                    self.update_product = False

    @api.onchange('selected')
    def _selected_onchange(self):
        if self.selected:
            for line in self.product_line_ids:
                line.selected = True
        else:
            for line in self.product_line_ids:
                line.selected = False
        self._amount_all()

    def _amount_all(self):
        amount_untaxed = 0.0
        amount_tax = 0.0
        amount_total = 0.0
        for line in self.product_line_ids:
            str_id = str(line.id)
            if line.selected == True and 'virtual' in str_id:
                line_amount_untaxed = line.subtotal
                line_amount_tax = line.price_tax
                line_amount_total = line.net_price
                
                amount_untaxed += line_amount_untaxed
                amount_tax += line_amount_tax
                amount_total += line_amount_total

        self.amount_untaxed = amount_untaxed
        self.amount_tax = amount_tax
        self.amount_total = amount_total

    @api.onchange("update_total")
    def _onchange_update_total(self):
        if self.update_total == True:
            self._amount_all()
            self.update_total = False
    
class WizardSplitReceiptINLine(models.TransientModel):
    _name = "wizard.split.receipt.in.line"
    _description = "Wizard Split Receipt IN Line"

    wiz_id = fields.Many2one("wizard.split.receipt.in")
    move_id = fields.Many2one(comodel_name="stock.move", string="Stock Move")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    picking_id = fields.Many2one(related='wiz_id.picking_id.purchase_id',string="Source Document")
    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', required=True)
    po_remain = fields.Float(string="PO Demand")
    po_receive_qty = fields.Float(string="PO Receipted QTY")
    po_product_uom = fields.Many2one(comodel_name="uom.uom", string="PO UOM", readonly=True)
    product_uom_qty = fields.Float(string="Demand")
    receive_qty = fields.Float(string="Receipted QTY")
    product_uom = fields.Many2one(comodel_name="uom.uom", string="UOM", readonly=True)
    selected = fields.Boolean(string="Select")
    price_unit = fields.Float(string="Unit Price", digits='Product Price',default=0)
    currency_id = fields.Many2one('res.currency', string='Currency',)
    taxes_id = fields.Many2many('account.tax', string='Taxes',)
    subtotal = fields.Monetary(compute='_compute_amount', string="Subtotal")
    price_tax = fields.Float(compute='_compute_amount', string='Tax')
    net_price = fields.Monetary(compute='_compute_amount', string="Net Price")

    def convert_uom_factor(self, product=False, qty=0, move_po_uom=False):

        if not (product and qty and move_po_uom):
            qty = 0
            return qty

        base_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_type == "base" and l.product_id.id == product.id
        )
        if not base_map:  # ตรวจว่ามี factor, uom ที่ base มั้ย
            qty = 0
            return qty
        
        base_uom = base_map[0].uom_id

        po_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_id.id == move_po_uom.id and l.product_id.id == product.id
        )
        if (
            not po_map or not po_map[0].factor_base
        ):  # ตรวจว่ามี factor, uom ที่เราส่งมามั้ย
            qty = 0
            sale_line_uom = False
            return qty, sale_line_uom

        factor = po_map[0].factor_base
        product_qty_f = qty * factor

        return product_qty_f
    
    def convert_uom_factor_po(self, product=False, qty=0, move_po_uom=False):
        po_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_id.id == move_po_uom.id and l.product_id.id == product.id
        )
        if (
            not po_map or not po_map[0].factor_base
        ):  # ตรวจว่ามี factor, uom ที่เราส่งมามั้ย
            qty = 0
            return qty

        factor = po_map[0].factor_base
        if factor != 0:
            product_qty_f = qty / factor
        else:
            product_qty_f = 0

        return product_qty_f
    
    @api.onchange("po_receive_qty")
    def _onchange_po_receive_qty(self):
        if self.po_receive_qty > self.po_remain:
            raise ValidationError(_('กรุณาตรวจสอบจำนวนสินค้า ที่ทำการรับเนื่องจากระบบตรวจพบว่าจำนวนเกินกว่า PO ที่กำหนด'))
        
        if not self.env.context.get('from_receive_qty'):
            self = self.with_context(from_po_receive_qty=True)
            product_qty_f = self.po_receive_qty
            if self.po_product_uom.id != self.product_uom.id:
                product_qty_f = self.convert_uom_factor(
                        self.product_id, self.po_receive_qty, self.po_product_uom
                    )
            self.receive_qty = product_qty_f
            self._compute_amount()

    @api.onchange("receive_qty")
    def _onchange_receive_qty(self):
        if not self.env.context.get('from_po_receive_qty'):
            self = self.with_context(from_receive_qty=True)
            product_qty_f = self.receive_qty
            if self.po_product_uom.id != self.product_uom.id:
                product_qty_f = self.convert_uom_factor_po(
                        self.product_id, self.receive_qty, self.po_product_uom
                    )
            self.po_receive_qty = product_qty_f
            self._compute_amount()

    def _prepare_compute_all_values(self):
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency_id': self.currency_id,
            'product_qty': self.po_receive_qty,
            'product': self.product_id,
            'partner': self.move_id.picking_id.partner_id,
        }
    
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'net_price': taxes['total_included'],
                'subtotal': taxes['total_excluded'],
            })