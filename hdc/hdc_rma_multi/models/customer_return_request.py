from odoo import api, fields, models, _
from odoo.exceptions import UserError

READONLY_STATES = {
    "draft": [("readonly", False)],
    "confirm": [("readonly", True)],
    "done": [("readonly", True)],
}

class CustomerReturnRequest(models.Model):
    _name = "customer.return.request"
    _description = "customer.return.request"
    _order = "name desc"

    name = fields.Char(string = 'Customer Return Request', readonly=True, index=True, copy=False, default=lambda self: _('New'))
    return_request_lines = fields.One2many(
        comodel_name="customer.return.request.line",
        inverse_name="return_request_id",
        string="Product Lines",
        copy=False
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=True,
        states=READONLY_STATES,
    )
    partner_address_id = fields.Many2one(
        comodel_name="res.partner",
        string="Address",
        states=READONLY_STATES,
    )
    date = fields.Datetime(string="Received Date", default=lambda self: fields.Datetime.now())
    user_id = fields.Many2one('res.users', string='Responsed By', default=lambda self: self.env.user, required=True)
    receive_method_id = fields.Many2one(comodel_name="receive.method", string="Received Method")
    receive_by = fields.Char(string="Received By")
    location_id = fields.Many2one('stock.location', string='Return Location', required=True, domain=[('center_return_location', '=', True)])
    state = fields.Selection(
        selection=[("draft", "Draft"), ("confirm", "Confirm"), ("done", "Done"), ("cancel", "Cancel")],
        string="State",
        default="draft",
        readonly=True,
    )
    rma_count = fields.Integer('RMA Claims', compute='_compute_rma_count')
    is_modern_trede = fields.Boolean('Modern Trade',default=False,states=READONLY_STATES,)

    @api.model
    def _get_domain_picking_type_id(self):
        addition_operation_type = self.env["addition.operation.type"].search([("code", "=", "AO-05")], limit=1)
        picking_type_id = self.env['stock.picking.type'].search([
            ("addition_operation_types", "=", addition_operation_type.id),("is_rg","=",True)
        ])
        return [('id','in',picking_type_id.ids)]
    
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type',domain=lambda self: self._get_domain_picking_type_id())
    remark = fields.Text(string='Remark')
    return_count = fields.Integer('Return', compute='_compute_return_count')
    customer_requisition = fields.Char(string='Customer Requisition')
    customer_ref = fields.Char(string='Customer Reference')

    # 28-11-2024 มีเปลี่ยนไปเอาจาก picking_type_id (Operation Type) แทน 
    # @api.model
    # def _default_location_id(self):
    #     # Find the first location that matches the domain condition
    #     location = self.env['stock.location'].search([('center_return_location', '=', True)], limit=1)
    #     return location.id if location else False
    
    def _compute_rma_count(self):
        """
        This method used to RMA count. It will display on the sale order screen.
        """
        for order in self:
            order.rma_count = self.env['crm.claim.ept'].search_count \
                ([('return_request_id', '=', order.id)])
            
    def _compute_return_count(self):
        for order in self:
            order.return_count = self.env['stock.picking'].search_count \
                ([("origin", "=", order.name)])

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('customer_return_request_sequence') or _('New')
        result = super(CustomerReturnRequest, self).create(vals)
        return result
    
    def action_confirm(self):
        self.write({"state": "confirm"})
        # 2/12/2024 มีปรับ การทำงานใหม่ ไม่มีสร้างใบรับเมื่อ confirm
        # if self.picking_type_id:
        #     new_picking = self.env['stock.picking'].create({
        #                     'partner_id': self.partner_id.id,
        #                     'picking_type_id': self.picking_type_id.id,
        #                     'state': 'draft',
        #                     'origin': self.name,
        #                     'location_id': self.picking_type_id.default_location_src_id.id,
        #                     'location_dest_id': self.picking_type_id.default_location_dest_id.id,
        #                     })
        #     for line in self.return_request_lines:  # วนลูปสำหรับสินค้าแต่ละรายการ
        #             move = self.env['stock.move'].create({
        #                 'name': line.product_id.name,
        #                 'product_id': line.product_id.id,
        #                 'product_uom_qty': line.receive_qty,  # จำนวนสินค้า
        #                 'product_uom': line.product_id.uom_id.id,
        #                 'location_id': self.picking_type_id.default_location_src_id.id,
        #                 'location_dest_id': self.picking_type_id.default_location_dest_id.id,
        #                 'picking_id': new_picking.id,  # ระบุใบ Picking ที่เพิ่งสร้าง
        #                 'origin': self.name,
        #                 'state': 'draft',
        #             })
    
    def action_print(self):
        print("action_print")
    
    def action_create_rma(self):
        if self.return_request_lines:
            order_line = []
            for product in self.return_request_lines:
                if product.receive_qty == 0:
                    raise UserError(_("กรุณาระบุจำนวน Receive ก่อนทำการกด Create RMA"))
                if product.rma_qty < product.receive_qty or self.is_modern_trede:
                    line = (0, 0, {
                        'wiz_id': self.id,
                        'product_id': product.product_id.id,
                        'name': product.name,
                        'invoice_id': product.invoice_id.id,
                        'delivery_id': product.delivery_id.id,
                        'sale_id': product.sale_id,
                        'receive_qty': product.receive_qty,
                        'quantity': product.receive_qty - product.rma_qty,
                        'rma_qty': product.rma_qty,
                        'uom': product.uom.id,
                        'remark': product.remark,
                        'return_request_line': product.id
                        })
                    order_line.append(line)
                
            if order_line:
                return {
                        'name': "Create RMA",
                        'view_mode': 'form',
                        'res_model': 'wizard.create.multi.rma',
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': {
                            'default_name': self.name,
                            'default_return_request_id': self.id,
                            'default_partner_id': self.partner_id.id,
                            # 'default_partner_address_id': self.partner_address_id.id,
                            'default_is_modern_trede': self.is_modern_trede,
                            # 'default_location_id': self.location_id.id,
                            'default_customer_requisition': self.customer_requisition,
                            'default_customer_ref': self.customer_ref,
                            'default_product_line_ids': order_line
                        }
                    }
            else:
                raise UserError(_("มีการทำ RMA ครบแล้ว"))
    
    def action_cancel(self):
        self.ensure_one()
        if self.state not in ('draft', 'confirm'):
            raise UserError(_("You can only cancel a CRR in Draft or Confirm state."))

        # Show confirmation dialog
        message = _("Do you need to cancel the transaction on the CRR page? Please note that once it is cancelled, you will not be able to use the same form again.")
        if self.env.context.get('lang') == 'th_TH':
            message = _("ต้องยกเลิกการทำรายการหน้า CRR ใช่หรือไม่ กรณีที่ท่านยกเลิกแล้ว จะไม่สามารถกลับมาใช้งานที่ใบเดิมได้")

        remaining_lines = self.return_request_lines.filtered(
            lambda l: l.receive_done > 0
        )

        if remaining_lines:
            raise UserError(_("Cannot cancel because there are still items that have not been fully received. Please complete all item receipts before cancelling."))

        return {
            'name': _('Warning'),
            'type': 'ir.actions.act_window',
            'res_model': 'crr.cancel.confirmation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_crr_id': self.id,
                'default_message': message,
            }
        }

    def action_force_done(self):
        self.ensure_one()
        if self.state != 'confirm':
            raise UserError(_("You can only force close a CRR in Confirm state."))

        remaining_lines = self.return_request_lines.filtered(
            lambda l: l.receive_qty > l.rma_qty
        )
        
        message = _("Do you need to close the transaction on the CRR page? Please note that once the process is closed, you will not be able to use the same form again. The system will generate a return form for the remaining items for you to notify the customer accordingly.")
        if self.env.context.get('lang') == 'th_TH':
            message = _("ต้องปิดจบการทำรายการหน้า CRR ใช่หรือไม่ กรณีที่ท่านปิดจบการทำงานแล้ว จะไม่สามารถกลับมาใช้งานที่ใบเดิมได้ ระบบจะสร้างใบส่งคืนสินค้าที่เหลือให้ทานนำแจ้งคืนกลับลูกค้า")

        return {
            'name': _('Warning'),
            'type': 'ir.actions.act_window',
            'res_model': 'crr.force.done.confirmation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_crr_id': self.id,
                'default_message': message,
                'default_has_remaining_items': bool(remaining_lines),
            }
        }


    
    def action_view_rma(self):
        return {
            "name": _("RMA"),
            "view_mode": "tree,form",
            "res_model": "crm.claim.ept",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("return_request_id", "=", self.id)],
        }
    
    @api.onchange('return_request_lines')
    def _onchange_return_request_lines(self):
        for rec in self:
            if rec.state == 'confirm':
                if all(line.rma_qty > 0 and line.rma_qty == line.receive_qty for line in rec.return_request_lines):
                    rec.state = 'done'

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        self.location_id = self.picking_type_id.default_location_dest_id.id

    def action_view_return(self):
        return {
            "name": _("Return Customer"),
            "view_mode": "tree,form",
            "res_model": "stock.picking",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("origin", "=", self.name)],
        }
    
    def action_create_receive(self):
        context = {
            'default_return_request_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_company_chain_id': self.partner_id.company_chain_id.id,
        }
        return {
                'type': 'ir.actions.act_window',
                'name': 'Wizard Create Receive',
                'res_model': 'wizard.add.product.crr',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    #เอามาจับตอนขึ้นภาษาไทย - อังกฤษ
    lang_code = fields.Char(
        string='Language Code',
        compute='_compute_lang_code',
        store=False
    )

    def _compute_lang_code(self):
        for rec in self:
            rec.lang_code = self.env.context.get('lang') or False

    def re_compute_rma_qty(self):
        for rec in self:
            rma_ids = self.env['crm.claim.ept'].search([('return_request_id', '=', rec.id),('state','!=','reject')])
            for rma in rec.return_request_lines:
                rma_qty = sum(rma_ids.mapped('claim_line_ids').filtered(lambda a: a.product_id.id == rma.product_id.id).mapped('quantity'))
                rma.rma_qty = rma_qty
                rma._compute_remain_qty()
            if any(line.rma_qty != line.receive_qty for line in rec.return_request_lines):
                rec.state = 'confirm'
    
class CustomerReturnRequestLine(models.Model):
    _name = "customer.return.request.line"
    _description = "Customer Return Request Line"

    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    name = fields.Text(string="Description")
    invoice_id = fields.Many2one(comodel_name="account.move", string="Invoice No")
    delivery_id = fields.Many2one(comodel_name="stock.picking", string="Delivery No")
    sale_id = fields.Char(string="SO No")
    receive_qty = fields.Float(string="Demand Receive")
    
    # quantity = fields.Float(string="Quantity")
    rma_qty = fields.Float(string="RMA QTY", copy=False)
    uom = fields.Many2one(comodel_name="uom.uom", string="UOM", required=True)
    remark = fields.Text(string="Remarks")
    return_request_id = fields.Many2one(comodel_name="customer.return.request", string="Return Request")
    state = fields.Selection(
        selection=[("draft", "Draft"), ("created_rma", "Created RMA"), ("done", "Done")],
        string="State",
        default="draft",
        readonly=True,
        copy=False
    )
    on_hand_qty_rg = fields.Float(string="On Hand RG", compute="_compute_on_hand_qty_rg")

    def _compute_on_hand_qty_rg(self):
        for order in self:
            order.on_hand_qty_rg = self.env['stock.quant'].search([ ("product_id", "=", order.product_id.id),
                                                                    ("location_id", "=", order.return_request_id.location_id.id),
                                                                    ("quantity", ">", 0)]).quantity

    def _compute_receive_done(self):
        for order in self:
            move_list = self.env['stock.move'].search([("origin", "=", order.return_request_id.name),("product_id","=",order.product_id.id),('state','=','done')])
            move_done = 0
            
            for move in move_list:
                picking_type = move.picking_id.picking_type_id.code
                if picking_type == "incoming":
                    move_done += move.quantity_done
                elif picking_type == "outgoing":
                    move_done -= move.quantity_done

            order.receive_done = move_done

    receive_done = fields.Float(string="Receive Done",compute='_compute_receive_done')

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        self.name = self.product_id.display_name
        self.uom = self.product_id.uom_id.id

    @api.depends('receive_qty', 'rma_qty')
    def _compute_remain_qty(self):
        for line in self:
            line.remain_qty = (line.receive_qty or 0.0) - (line.rma_qty or 0.0)

    remain_qty = fields.Float(string="Remain QTY", compute="_compute_remain_qty", store=True, readonly=True,
                              help="Calculated from Demand Receive - RMA QTY to show how many items are left for RMA.")