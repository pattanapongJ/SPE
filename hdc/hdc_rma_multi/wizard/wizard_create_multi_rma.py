from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class CreateMultipleRma(models.TransientModel):
    _name = "wizard.create.multi.rma"
    _description = "Wizard Create Multi RMA"

    name =  fields.Char()
    return_request_id = fields.Many2one(comodel_name="customer.return.request")
    rma_reason_id = fields.Many2one('rma.reason.ept', string="Customer Reason", required=True, copy=False)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=True,
    )
    partner_address_id = fields.Many2one(
        comodel_name="res.partner",
        string="Address",
    )

    customer_requisition = fields.Char(string='Customer Requisition')
    customer_ref = fields.Char(string='Customer Reference')
    no_invoice = fields.Boolean(string='No Invoice Ref.')

    @api.model
    def _default_company_id(self):
        return self.env.company
    
    product_line_ids = fields.One2many('wizard.create.multi.rma.line', 'wiz_id')
    # location_id = fields.Many2one('stock.location', related='return_request_id.location_id', string='Return Location')
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=True, default=lambda self: self._default_company_id(),)
    location_id = fields.Many2one('stock.location', string='Return Location')
    sale_id = fields.Many2one('sale.order' ,string="SO No")
    invoice_id = fields.Many2one(comodel_name="account.move", string="Invoice No")
    delivery_id = fields.Many2one(comodel_name="stock.picking", string="Delivery No")
    is_modern_trede = fields.Boolean('Modern Trade')
    spe_invoice = fields.Many2one(
        'account.move',
        string="SPE Invoice",
        domain="[('id', 'in', available_invoice_ids), ('state', '=', 'posted')]"
    )
    
    available_invoice_ids = fields.Many2many(
        'account.move',
        compute='_compute_available_invoices',
        store=False
    )

    def get_valid_invoices(self):
        if self.partner_id.parent_id:
            partner_ids = self.env['res.partner'].search([('parent_id', '=', self.partner_id.parent_id.id)]).ids
            partner_ids.append(self.partner_id.parent_id.id)
        else:
            partner_ids = self.env['res.partner'].search([('parent_id', '=', self.partner_id.id)]).ids
            partner_ids.append(self.partner_id.id)

        domains_check = {
            'invoice_id': [('partner_id', 'in', partner_ids), 
                            ('move_type', '=', 'out_invoice'), 
                            ('state', '=', 'posted'), 
                            ('company_id', '=', self.company_id.id)],
        }
        # ตรวจสอบสินค้าที่เคยถูกคืนแล้วใน RMA พร้อม account_id ที่เกี่ยวข้อง
        rma_lines = self.env['crm.claim.ept'].search([('partner_id', 'in', partner_ids), 
                                                    ('company_id', '=', self.company_id.id)])
        returned_quantities = {}

        # เก็บจำนวนสินค้าที่ถูกคืนแล้ว แยกตาม account_id
        for rma in rma_lines:
            account_id = rma.account_id.id
            if account_id not in returned_quantities:
                returned_quantities[account_id] = {}
            for line in rma.claim_line_ids:
                product_id = line.product_id.id
                if product_id not in returned_quantities[account_id]:
                    returned_quantities[account_id][product_id] = 0
                returned_quantities[account_id][product_id] += line.quantity

        # กรองใบแจ้งหนี้ที่ยังมีสินค้าที่คืนไม่ครบ
        invoices = self.env['account.move'].search(domains_check['invoice_id'])
        valid_invoices = []
        for invoice in invoices:
            if not self.is_modern_trede and not invoice.invoice_origin:
                continue
            
            # ดึง account_id ของใบแจ้งหนี้เพื่อตรวจสอบจำนวนที่คืนแล้ว
            account_id = invoice.id
            has_remaining_qty = False
            for line in invoice.invoice_line_ids:
                product_id = line.product_id.id
                delivered_qty = line.quantity
                returned_qty = returned_quantities.get(account_id, {}).get(product_id, 0)

                # ถ้าสินค้ายังไม่ได้คืนครบ
                if delivered_qty > returned_qty:
                    has_remaining_qty = True
                    break

            # ถ้าใบแจ้งหนี้นี้ยังมีสินค้าที่สามารถคืนได้
            if has_remaining_qty:
                valid_invoices.append(invoice.id)
        return valid_invoices
    
    @api.depends('invoice_id', 'spe_invoice')
    def _compute_available_invoices(self):
        for rec in self:
            valid_invoices = self.get_valid_invoices()
            domain = [('form_no', '!=', False),('id', 'in', valid_invoices)]
            if rec.invoice_id:
                domain = ['|'] + domain + [
                    ('id', '=', rec.invoice_id.id),
                    ('old_spe_invoice', '=', rec.invoice_id.form_no),
                ]
            elif rec.spe_invoice:
                domain = ['|'] + domain + [
                    ('form_no', '=', rec.spe_invoice.form_no),
                    ('old_spe_invoice', '=', rec.spe_invoice.form_no),
                ]
            rec.available_invoice_ids = self.env['account.move'].search(domain).ids

    @api.onchange('invoice_id')
    def _onchange_invoice_id_sync_spe_invoice(self):
        if self.invoice_id:
            if self.invoice_id.form_no:
                spe_invoice = self.env['account.move'].search([
                    '&',
                    ('state', '=', 'posted'),
                    '|',
                    ('form_no', '=', self.invoice_id.form_no),
                    ('old_spe_invoice', '=', self.invoice_id.form_no),
                ], limit=1)

                if spe_invoice:
                    self.spe_invoice = spe_invoice

            return {
                'domain': {
                    'spe_invoice': [
                        '&', ('state', '=', 'posted'),
                        '|',
                        ('form_no', '=', self.invoice_id.form_no),
                        ('old_spe_invoice', '=', self.invoice_id.form_no),
                    ]
                }
            }
        else:
            self.spe_invoice = False
            valid_invoices = self.get_valid_invoices()
            return {
                'domain': {
                    'spe_invoice': [
                        ('form_no', '!=', False),
                        ('state', '=', 'posted'),
                        ('id', 'in', valid_invoices),
                    ]
                }
            }

    @api.onchange('rma_reason_id')
    def _onchange_rma_reason_id(self):
        domains = {
            'rma_reason_id': []
        }
        if self.is_modern_trede :
            domains.update({
                'rma_reason_id': [('is_select_product_receipt', '=', True)]
            })
        return {'domain': domains}
    
    @api.onchange('company_id', 'sale_id', 'invoice_id', 'delivery_id','spe_invoice')
    def _onchange_fields(self):
        if self.partner_id.parent_id:
            partner_ids = self.env['res.partner'].search([('parent_id', '=', self.partner_id.parent_id.id)]).ids
            partner_ids.append(self.partner_id.parent_id.id)
        else:
            partner_ids = self.env['res.partner'].search([('parent_id', '=', self.partner_id.id)]).ids
            partner_ids.append(self.partner_id.id)

        # เริ่มต้นการกรองใบแจ้งหนี้ (invoice_id)
        domains = {
            'invoice_id': [('partner_id', 'in', partner_ids), 
                            ('move_type', '=', 'out_invoice'), 
                            ('state', '=', 'posted'), 
                            ('company_id', '=', self.company_id.id)],
            'delivery_id': [('partner_id', 'in', partner_ids), 
                            ('state', '=', 'done'), 
                            ('company_id', '=', self.company_id.id)],
            'sale_id': [('partner_id', 'in', partner_ids), 
                        ('state', 'in', ['done', 'sale']), 
                        ('company_id', '=', self.company_id.id)],
            'location_id': [('usage', '=', 'internal'), 
                            ('return_location', '=', True), 
                            ('company_id', '=', self.company_id.id)]
        }

        # กรณีที่เป็น Modern Trade
        if self.is_modern_trede:
            return {'domain': domains}

        # ตรวจสอบสินค้าที่เคยถูกคืนแล้วใน RMA พร้อม account_id ที่เกี่ยวข้อง
        rma_lines = self.env['crm.claim.ept'].search([('partner_id', 'in', partner_ids), 
                                                    ('company_id', '=', self.company_id.id)])
        returned_quantities = {}

        # เก็บจำนวนสินค้าที่ถูกคืนแล้ว แยกตาม account_id
        for rma in rma_lines:
            account_id = rma.account_id.id
            if account_id not in returned_quantities:
                returned_quantities[account_id] = {}
            for line in rma.claim_line_ids:
                product_id = line.product_id.id
                if product_id not in returned_quantities[account_id]:
                    returned_quantities[account_id][product_id] = 0
                returned_quantities[account_id][product_id] += line.quantity

        # กรองใบแจ้งหนี้ที่ยังมีสินค้าที่คืนไม่ครบ
        invoices = self.env['account.move'].search(domains['invoice_id'])
        valid_invoices = []
        for invoice in invoices:
            if not self.is_modern_trede and not invoice.invoice_origin:
                continue
            
            # ดึง account_id ของใบแจ้งหนี้เพื่อตรวจสอบจำนวนที่คืนแล้ว
            account_id = invoice.id
            has_remaining_qty = False
            for line in invoice.invoice_line_ids:
                product_id = line.product_id.id
                delivered_qty = line.quantity
                returned_qty = returned_quantities.get(account_id, {}).get(product_id, 0)

                # ถ้าสินค้ายังไม่ได้คืนครบ
                if delivered_qty > returned_qty:
                    has_remaining_qty = True
                    break

            # ถ้าใบแจ้งหนี้นี้ยังมีสินค้าที่สามารถคืนได้
            if has_remaining_qty:
                valid_invoices.append(invoice.id)

        # อัปเดต domain ของ invoice_id ให้กรองตามสินค้าที่คืนไม่ครบ
        domains['invoice_id'] = [('id', 'in', valid_invoices)]

        returned_quantities_sale_id = {}

        # เก็บจำนวนสินค้าที่ถูกคืนแล้ว แยกตาม account_id
        for rma in rma_lines:
            sale_id = rma.sale_id.id
            if sale_id not in returned_quantities_sale_id:
                returned_quantities_sale_id[sale_id] = {}
            for line in rma.claim_line_ids:
                product_id = line.product_id.id
                if product_id not in returned_quantities_sale_id[sale_id]:
                    returned_quantities_sale_id[sale_id][product_id] = 0
                returned_quantities_sale_id[sale_id][product_id] += line.quantity

        # กรณีกรองตาม sale_id
        sale_orders = self.env['sale.order'].search(domains['sale_id'])
        valid_sales = []
        for sale_order in sale_orders:
            # ดึง account_id ของ sale order เพื่อตรวจสอบการคืนสินค้าที่เกี่ยวข้อง
            sale = sale_order.id
            has_remaining_qty = False
            for line in sale_order.order_line:
                product_id = line.product_id.id
                ordered_qty = line.product_uom_qty
                returned_qty = returned_quantities_sale_id.get(sale, {}).get(product_id, 0)

                # ถ้าสินค้ายังไม่ได้คืนครบ
                if ordered_qty > returned_qty:
                    has_remaining_qty = True
                    break

            # ถ้าสินค้าที่ยังไม่ได้คืนครบ
            if has_remaining_qty:
                valid_sales.append(sale_order.id)

        domains['sale_id'] = [('id', 'in', valid_sales)]

        returned_quantities_delivery = {}

        # เก็บจำนวนสินค้าที่ถูกคืนแล้ว แยกตาม account_id
        for rma in rma_lines:
            picking_id = rma.picking_id.id
            if picking_id not in returned_quantities_delivery:
                returned_quantities_delivery[picking_id] = {}
            for line in rma.claim_line_ids:
                product_id = line.product_id.id
                if product_id not in returned_quantities_delivery[picking_id]:
                    returned_quantities_delivery[picking_id][product_id] = 0
                returned_quantities_delivery[picking_id][product_id] += line.quantity

        # กรณีกรองตาม delivery_id
        deliveries = self.env['stock.picking'].search(domains['delivery_id'])
        valid_deliveries = []
        for delivery in deliveries:
            # ดึง account_id ของ delivery เพื่อตรวจสอบการคืนสินค้าที่เกี่ยวข้อง
            picking = delivery.id
            has_remaining_qty = False
            for line in delivery.move_lines:
                product_id = line.product_id.id
                delivered_qty = line.product_uom_qty
                returned_qty = returned_quantities_delivery.get(picking, {}).get(product_id, 0)

                # ถ้าสินค้ายังไม่ได้คืนครบ
                if delivered_qty > returned_qty:
                    has_remaining_qty = True
                    break

            # ถ้ายังมีสินค้าที่สามารถคืนได้
            if has_remaining_qty:
                valid_deliveries.append(delivery.id)

        domains['delivery_id'] = [('id', 'in', valid_deliveries)]

        # เพิ่มการกรอง กรณี SPE Invoice
        if self.spe_invoice:
            self.invoice_id = self.spe_invoice.id
            invoice_ids = self.env['account.move'].search([
                '&',
                ('state', '=', 'posted'),
                '|',
                ('form_no', '=', self.spe_invoice.form_no),
                ('old_spe_invoice', '=', self.spe_invoice.form_no),
            ]).ids
            domains.update({'invoice_id': [('id', 'in', invoice_ids)]})

        # กรณีกรองตาม invoice_id ที่มี invoice_origin ไม่ว่าง
        if self.invoice_id and self.invoice_id.invoice_origin:
            sale_ids = self.env['sale.order'].search([
                ('partner_id', 'in', partner_ids),
                ('name', '=', self.invoice_id.invoice_origin),
                ('state', 'in', ['done', 'sale']),
                ('company_id', '=', self.company_id.id),
            ]).ids
            delivery_ids = self.env['stock.picking'].search([
                ('origin', '=', self.invoice_id.invoice_origin),
                ('state', '=', 'done'),
                ('id', 'in', valid_deliveries),
                ('company_id', '=', self.company_id.id),
            ]).ids

            domains.update({'sale_id': [('id', 'in', sale_ids)]})
            domains.update({'delivery_id': [('id', 'in', delivery_ids)]})

        if self.sale_id:
            invoice_ids = self.env['account.move'].search([
                ('partner_id', 'in', partner_ids),
                ('invoice_origin', '=', self.sale_id.name),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'), 
                ('id', 'in', valid_invoices),
                ('company_id', '=', self.company_id.id),
            ]).ids
            delivery_ids = self.env['stock.picking'].search([
                ('sale_id', '=', self.sale_id.id),
                ('state', '=', 'done'),
                ('id', 'in', valid_deliveries),
                ('company_id', '=', self.company_id.id),
            ]).ids
            domains.update({
                'invoice_id': [('id', 'in', invoice_ids)],
                'delivery_id': [('id', 'in', delivery_ids)]
            })
        if self.delivery_id:
            sale_ids = [self.delivery_id.sale_id.id] if self.delivery_id.sale_id else []
            invoice_ids = self.env['account.move'].search([
                ('invoice_origin', '=', self.delivery_id.origin),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'), 
                ('id', 'in', valid_invoices),
                ('company_id', '=', self.company_id.id),
            ]).ids
            domains.update({'sale_id': [('id', 'in', sale_ids)]})
            domains.update({'invoice_id': [('id', 'in', invoice_ids)]})

        # คืนค่า domain ที่กรองแล้ว
        return {'domain': domains}

    def action_create_rma(self):
        crr = self.env["customer.return.request"]
        crr_id = crr.browse(self.env.context.get("active_id"))
        if self.product_line_ids:
            zero_choose = True
            has_line_data = False
            is_modern_trede = self.is_modern_trede
            claim_line_ids = []
            if not self.no_invoice:
                for line in self.product_line_ids:
                    if line.choose:
                        zero_choose = False
                        check_no_related = True
                        sale_id = self.sale_id
                        if sale_id or is_modern_trede:
                            picking_id = self.env['stock.picking'].search([('id', '=', self.delivery_id.id),('state', '=', 'done'),('origin', '=', self.sale_id.name)],limit = 1)
                            if picking_id or is_modern_trede:
                                check_no_related = False
                                claim_lines = []
                                claim_lines_search = []
                                move_line_product = self.product_line_ids
                                quantity = line.quantity
                                if self.delivery_id and line.product_id and not is_modern_trede:
                                    returned_qty = 0
                                    for move_id in self.delivery_id.move_lines:
                                        """This previous_claimline_ids is checking that already claim is created
                                        for this product based on previous claim we can add returned_qty on 
                                        created claim"""
                                        previous_claimline_ids = self.env['claim.line.ept'].search([
                                            ('move_id', '=', move_id.id), ('product_id', '=', move_id.product_id.id)])
                                        returned_qty = 0
                                        if previous_claimline_ids:
                                            for line_id in previous_claimline_ids:
                                                returned_qty += line_id.quantity
                                                if line_id.serial_lot_ids:
                                                    claim_lines_search.append({
                                                        'product_id':line_id.product_id.id, 'qty':line_id.quantity, 'lot_id': line_id.serial_lot_ids.ids[0]})

                                        claim_line_data = self.check_return_qty(returned_qty, move_id, claim_lines, claim_lines_search, quantity, move_line_product, is_modern_trede)
                                        if claim_line_data:
                                            has_line_data = True
                                            claim_line_ids = [(5, 0, 0)] + claim_line_data
                                else:
                                    claim_line_data = self.check_return_qty(0, line, claim_lines, claim_lines_search, quantity, move_line_product, is_modern_trede)
                                    if claim_line_data:
                                        has_line_data = True
                                        claim_line_ids = [(5, 0, 0)] + claim_line_data
            else:
                claim_lines = []
                claim_lines_search = []
                for line in self.product_line_ids:
                    if line.choose:
                        zero_choose = False
                        quantity = line.quantity
                        claim_lines.append((0, 0, {
                                            'product_id':line.product_id.id, 'done_qty_update': quantity, 'quantity':quantity, 'move_id':False}))
                        if claim_lines:
                            has_line_data = True
                            claim_line_ids = [(5, 0, 0)] + claim_lines

            if zero_choose:
                raise UserError(_("Please select at least 1 item."))
            if has_line_data:
                data = {
                    "name": self.name,
                    "return_request_id": self.return_request_id.id,
                    "rma_reason_id": self.rma_reason_id.id,
                    "customer_requisition":self.customer_requisition,
                    "customer_ref":self.customer_ref,
                    "claim_line_ids": claim_line_ids,
                    "spe_invoice":self.spe_invoice.id if self.spe_invoice else False,
                    "rma_reason_journal_id":self.rma_reason_id.journal_id.id if self.rma_reason_id.journal_id else False,
                }
                if not self.no_invoice:
                    data["account_id"] = self.invoice_id.id if self.invoice_id else False
                    data["picking_id"] = self.delivery_id.id if self.delivery_id else False
                    data["picking_ids"] = self.delivery_id.ids if self.delivery_id else False
                    data["sale_id"] = self.sale_id.id if self.sale_id else False
                else:
                    data["email_from"] = self.partner_id.email
                    data["partner_delivery_id"] = self.partner_id.id if self.partner_id else False
                    data["return_partner_delivery_id"] = self.partner_id.id if self.partner_id else False
                if self.sale_id.partner_shipping_id:
                    data["email_from"] = self.sale_id.partner_shipping_id.email
                    data["partner_delivery_id"] = self.sale_id.partner_shipping_id.id
                    data["return_partner_delivery_id"] = self.sale_id.partner_shipping_id.id
                if self.location_id:
                    data["location_id"] = self.location_id.id
                rma_id = self.env['crm.claim.ept'].create(data)
                for request_line in crr_id.return_request_lines:
                    for claim_line in self.product_line_ids.filtered(lambda l: l.choose is True):
                        if claim_line.product_id.id == request_line.product_id.id:
                            new_rma_qty = request_line.rma_qty + claim_line.quantity
                            data = {"rma_qty":  new_rma_qty}
                            request_line.write(data)
                crr_id._onchange_return_request_lines()

            else:
                raise UserError(_("No matching products found. Please check again."))
            
            
    
    @staticmethod
    def check_return_qty(returned_qty, move_id, claim_lines, claim_lines_search, quantity, move_line_product,is_modern_trede):
        """
        This method is used to check return quantity based on claim line.
        If previous claim is created then return qty count based on previous claim's return qty
        """
        claim_lines_std = []
        for line_prod in move_line_product:
            if line_prod.choose :
                if move_id and not is_modern_trede:
                    if line_prod.product_id.id == move_id.product_id.id:
                        if returned_qty < move_id.quantity_done or is_modern_trede:
                            qty = move_id.quantity_done - returned_qty
                            if qty > 0 and qty >= line_prod.quantity :
                                for line_id in move_id.move_line_ids :
                                    if line_id.lot_id:
                                        claim_lines_std.append((0, 0,{'product_id':move_id.product_id.id, 'done_qty': qty,
                                                                'qty':line_prod.quantity, 'move_id':move_id.id, 'lot_id': line_id.lot_id[0].id}))
                                    else:
                                        claim_lines.append((0, 0, {
                                                            'product_id':move_id.product_id.id, 'done_qty_update': qty, 'quantity':line_prod.quantity, 'move_id':move_id.id}))
                                if claim_lines_search:
                                    for line_search in claim_lines_search:
                                        for line in claim_lines_std:
                                            if line["product_id"] == line_search['product_id'] and line["lot_id"] == line_search['lot_id']:
                                                line["qty"] = line['qty'] - line_search['qty']
                                                break
                                for line_id in claim_lines_std:
                                        if line_id['qty'] > 0 :
                                            claim_lines.append((0, 0, {'product_id':line_id['product_id'], 'done_qty_update': line_id['done_qty'],
                                                                'quantity': line_id['qty'], 'move_id':line_id['move_id'], 'serial_lot_ids': [line_id['lot_id']]}))
                        if returned_qty > move_id.quantity_done :
                            raise UserError(_("Quantity is over, Please check Quantity again."))
                if is_modern_trede:
                    if line_prod.product_id.id == move_id.product_id.id:
                        qty = line_prod.quantity
                        claim_lines.append((0, 0, {
                                            'product_id':line_prod.product_id.id, 'done_qty_update': qty, 'quantity':line_prod.quantity, 'move_id':False}))
                                    

        return claim_lines


class CreateMultipleRmaLine(models.TransientModel):
    _name = "wizard.create.multi.rma.line"
    _description = "Wizard Create Multi RMA Line"

    wiz_id = fields.Many2one("wizard.create.multi.rma")
    return_request_line = fields.Many2one("customer.return.request.line")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    name = fields.Text(string="Description")
    invoice_id = fields.Many2one(comodel_name="account.move", string="Invoice No")
    delivery_id = fields.Many2one(comodel_name="stock.picking", string="Delivery No")
    sale_id = fields.Char(string="SO No")
    receive_qty = fields.Float(string="Receive")
    quantity = fields.Float(string="Quantity")
    rma_qty = fields.Float(string="RMA QTY")
    uom = fields.Many2one(comodel_name="uom.uom", string="UOM")
    remark = fields.Text(string="Remarks")
    choose = fields.Boolean(default=False)

    # @api.onchange('invoice_id')
    # def onchange_invoice_id(self):
    #     """This method is used to set default values in the RMA base on delivery changes."""
    #     claim_lines = []
    #     if self.invoice_id:
    #         self.change_field_based_on_account()
    #     else:
    #         self.sale_id = False
    #         self.delivery_id = False

    # def change_field_based_on_account(self):
    #     sale_id = self.env['sale.order'].search(
    #         [('invoice_ids', '=', self.invoice_id.id)], limit = 1)
    #     picking_ids = self.env['stock.picking'].search([('id', 'in', sale_id.picking_ids.ids),('state', '=', 'done'),('origin', '=', sale_id.name)], limit=1)
    #     # self.sale_id = sale_id.name
    #     self.delivery_id = picking_ids.id


