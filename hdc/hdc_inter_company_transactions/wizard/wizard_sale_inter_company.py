from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class WizardSaleInterCompany(models.TransientModel):
    _name = "wizard.sale.inter.company"
    _description = "Wizard.sale.inter.company"

    sale_id = fields.Many2one('sale.order', string = 'Sale Order')
    inter_company_transactions = fields.Boolean(related = "sale_id.inter_company_transactions")
    sale_type_check = fields.Boolean(related = "sale_id.type_id.inter_company_transactions")
    vendor_company_id = fields.Many2one('res.company', 'Company')
    vendor_id = fields.Many2one('res.partner', 'Vendor',domain=lambda self: self._get_domain_vendor_id())
    company_id = fields.Many2one('res.company', 'Company', default = lambda self: self.env.company)
    inter_company_id = fields.Many2one('res.company', 'Inter Company',domain=lambda self: self._get_domain_company_id(),)
    pricelist_id = fields.Many2one('product.pricelist', string = 'Pricelist', check_company = True,
        required = True, readonly = True,domain = "['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    date_order = fields.Datetime(string = 'Order Date', copy = False,default = fields.Datetime.now,)
    user_id = fields.Many2one('res.users', string = 'Responsible',
                              default = lambda self: self.env.user,)
    order_line = fields.One2many('wizard.sale.inter.company.line', 'wizard_sale_inter_company', string = 'SO Product List')
    order_po_line = fields.One2many('wizard.sale.inter.company.line.po', 'wizard_sale_inter_company', string = 'PO Product List')
    customer_id = fields.Many2one('res.partner', 'Customer',domain=lambda self: self._get_domain_customer_id())

    @api.model
    def _get_domain_vendor_id(self):
        selected_companies = self.env.context.get('allowed_company_ids', [])
        company = self.env['res.company'].browse(selected_companies)
        partner_list = []
        for com in company:
            partner_id = self.env['res.partner'].search([('inter_company_vendor', '=', True)])
            if partner_id:
                for vendor in partner_id:
                    partner_list.append(vendor.id)
        domain = [("id", "in", partner_list)]
        return domain
    
    @api.model
    def _get_domain_customer_id(self):
        selected_companies = self.env.context.get('allowed_company_ids', [])
        company = self.env['res.company'].browse(selected_companies)
        partner_list = []
        for com in company:
            partner_id = self.env['res.partner'].search([('inter_company_customer', '=', True)])
            if partner_id:
                for vendor in partner_id:
                    partner_list.append(vendor.id)
        domain = [("id", "in", partner_list)]
        return domain

    @api.model
    def _get_domain_company_id(self):
        selected_companies = self.env.context.get('allowed_company_ids', [])
        if self.env.company.id in selected_companies:
            selected_companies.remove(self.env.company.id)
        domain_inter_company_id = [("id", "in", selected_companies)]
        return domain_inter_company_id
    
    @api.onchange('inter_company_id', 'vendor_company_id')
    def onchange_inter_company_id(self):
        for line in self.order_line:
            if self.inter_company_transactions:
                res_product = line.product_id._compute_quantities_dict_company(lot_id = None, owner_id = None,
                                                                               package_id = None,
                                                                               company_id = self.sale_id.company_id)
                                                                            #    company_id = self.vendor_company_id)
                
            else:
                res_product = line.product_id._compute_quantities_dict_company(lot_id=None, owner_id=None,
                                                                               package_id=None,company_id=self.inter_company_id)
            free_qty = res_product[line.product_id.id]['free_qty']
            line.free_qty = free_qty
        
        for line in self.order_po_line:
            if self.inter_company_transactions:
                res_product = line.product_id._compute_quantities_dict_company(lot_id = None, owner_id = None,
                                                                                package_id = None,
                                                                              company_id = self.vendor_company_id)
                
            else:
                res_product = line.product_id._compute_quantities_dict_company(lot_id=None, owner_id=None,
                                                                               package_id=None,company_id=self.vendor_company_id)
            free_qty = res_product[line.product_id.id]['free_qty']
            line.free_qty = free_qty

    def create_sale_order(self):
        # partner_ids = self.env["res.partner"].search([('name', '=', self.company_id.name_th), ("customer", "=", True),("branch_number", "=", self.inter_company_id.branch_number)])
        # if not partner_ids:
        #     raise UserError(_("Not Customer"))
        # partner_id = partner_ids[-1]
        partner_id = self.customer_id
        addr = partner_id.address_get(['delivery', 'invoice'])
        partner_invoice_id = addr['invoice']
        partner_shipping_id = addr['delivery']
        type_id = self.env["sale.order.type"].search([('inter_company_transactions_type', '=', 'secondary_inter_company'), ("inter_company_transactions", "=", True), ("company_id", "=", self.inter_company_id.id)], limit=1)
        if not type_id:
            raise UserError(_("ไม่มี Sales Type ขายบริษัทในเครือ"))
        line_ids = []
        if self.order_line:
            for line in self.order_line:
                line_ids.append((0, 0, {
                    'product_id':line.product_id.id,
                    'name':line.product_id.get_product_multiline_description_sale(),
                    'product_uom_qty': line.order_qty,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'triple_discount': line.triple_discount if line.price_unit == line.cost_price_list and not line.free_product else '', # ถ้าแก้ไข unit price ไม่ตรงกับใน pricelist จะไม่ดึง discount กับ unit price pricelist มาให้
                    'discount_pricelist': line.unit_price_pricelist if line.price_unit == line.cost_price_list and not line.free_product else 0.0, # ถ้าแก้ไข unit price ไม่ตรงกับใน pricelist จะไม่ดึง discount กับ unit price pricelist มาให้
                    'free_product': line.free_product
                    }))
        delivery_trl = self.sale_id.delivery_trl
        delivery_trl_description = delivery_trl.name
        delivery_company = self.sale_id.delivery_company
        delivery_company_description = delivery_company.name

        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.inter_company_id.id)], limit=1)
        
        if type_id.warehouse_id:
            warehouse_id = type_id.warehouse_id
        branch_id = False
        if type_id.branch_id:
            branch_id = type_id.branch_id
        res_order = self.env["sale.order"].create({
            "partner_id": partner_id.id,
            "partner_invoice_id":partner_invoice_id,
            "partner_shipping_id": partner_shipping_id,
            "company_id":self.inter_company_id.id,
            "warehouse_id":warehouse_id.id,
            "type_id":type_id.id,
            "pricelist_id":type_id.pricelist_id.id,
            "delivery_trl":delivery_trl.id,
            "delivery_trl_description":delivery_trl_description,
            "delivery_company":delivery_company.id,
            "delivery_company_description":delivery_company_description,
            "order_line":line_ids,
            "inter_so_company": self.sale_id.name,
            "branch_id":branch_id.id,
            })
        res_order._onchange_pricelist_to_change_fiscal_position_id()
        res_order._amount_all()
        return res_order
    
    def create_purchase_order(self, res_order=None):
        if self.inter_company_transactions:
            order_type = self.env["purchase.order.type"].search(
                [('name', 'ilike', 'ระหว่างกัน'), ("inter_company_transactions", "=", True),
                 ("company_id", "=", self.vendor_company_id.id)])

        else:
            # partner_ids = self.env["res.partner"].search([('name', '=', self.inter_company_id.name_th), ("supplier", "=", True),("branch_number", "=", self.inter_company_id.branch_number)])
            # if not partner_ids:
            #     raise UserError(_("Not Supplier"))
            # partner_id = partner_ids[-1]
            partner_id = self.vendor_id
            order_type = self.env["purchase.order.type"].search([('name', 'ilike', 'ระหว่างกัน'), ("inter_company_transactions", "=", True), ("company_id", "=", self.company_id.id)])

        if not order_type:
            raise UserError(_("ไม่มี Purchase Type ระหว่างกัน"))
        if self.sale_id.type_id.inter_company_transactions:
            purchase_id = self.env["purchase.order"].search(
                [('origin', '=', self.sale_id.name), ("order_type", "=", order_type.id), ("state", "!=", "cancel")],limit = 1)
            if purchase_id:
                raise UserError(_("ระบบพบใบจัดซื้ออยู่แล้วอ้างอิง %s" %purchase_id.name))

        line_ids = []

        # Show Purchase Page And Inter Company Transactions = True
        if self.order_po_line and self.sale_type_check:
            for line in self.order_po_line:
                line_ids.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.display_name,
                    'product_qty': line.order_qty,
                    'product_uom': line.product_uom.id,
                    'gross_unit_price':line.price_unit,
                    'multi_disc': line.triple_discount if line.price_unit == line.cost_price_list and line.price_unit > 0 else '' # ถ้าแก้ไข unit price ไม่ตรงกับใน pricelist จะไม่ดึง discount กับ unit price pricelist มาให้
                    }))
        
        # Show Only Sale Page And Inter Company Transactions = False
        if self.order_po_line and self.order_line and not self.sale_type_check:
            for line in self.order_line:
                line_ids.append((0, 0, {
                    'product_id':line.product_id.id,
                    'name':line.product_id.display_name,
                    'product_qty': line.order_qty,
                    'product_uom': line.product_uom.id,
                    'gross_unit_price': line.price_unit,
                    'multi_disc': line.triple_discount if line.price_unit == line.cost_price_list and line.price_unit > 0 else '' # ถ้าแก้ไข unit price ไม่ตรงกับใน pricelist จะไม่ดึง discount กับ unit price pricelist มาให้
                    }))
        
        if self.inter_company_transactions:
            res_purchase = self.env["purchase.order"].create({
                "partner_id": self.vendor_id.id,
                "company_id": self.vendor_company_id.id,
                "order_type": order_type.id,
                "partner_ref": "-",
                "origin": res_order.name,
                "picking_type_id": order_type.picking_type_id.id,
                "order_line": line_ids,
                "inter_so_company": self.sale_id.name
                })
        else:
            res_purchase = self.env["purchase.order"].create({
                "partner_id": partner_id.id,
                "company_id":self.company_id.id,
                "order_type":order_type.id,
                "partner_ref": "-",
                "origin": res_order.name,
                "picking_type_id": order_type.picking_type_id.id,
                "order_line":line_ids,
                "inter_so_company": res_order.name
                })
        return res_purchase

    def check_available(self):
        if self.env.context.get('skip_pricelist_check'):
            return None

        products_no_pricelist = set()  # ใช้ set เพื่อป้องกันชื่อซ้ำ

        for line in self.order_line:
            if line.product_id.type == "product":
                if self.inter_company_transactions:
                    res_product = line.product_id._compute_quantities_dict_company(
                        lot_id=None, owner_id=None, package_id=None,
                        # company_id=self.vendor_company_id
                        company_id = self.sale_id.company_id
                    )
                else:
                    res_product = line.product_id._compute_quantities_dict_company(
                        lot_id=None, owner_id=None, package_id=None,
                        company_id=self.inter_company_id
                    )
                free_qty = res_product[line.product_id.id]['free_qty']
                if free_qty < line.product_uom_qty:
                    raise UserError(_("%s ของไม่เพียงพอ" % line.product_id.name))

            pricelist_item = self._get_applicable_pricelist_item(line.product_id, line.order_qty, self.pricelist_id)

            if not pricelist_item and not line.free_product:
                products_no_pricelist.add(line.product_id.name)

        if self.sale_type_check:
            for line in self.order_po_line:
                pricelist_item = self._get_applicable_pricelist_item(line.product_id, line.order_qty, self.pricelist_id)

                if not pricelist_item and not line.free_product:
                    products_no_pricelist.add(line.product_id.name)

        if products_no_pricelist and not self.env.context.get('skip_pricelist_check'):
            message = _("ไม่มีราคาซื้อขายระหว่างกัน กรุณาตรวจสอบใหม่อีกครั้ง \n %s" % ", ".join(products_no_pricelist))
            wizard = self.env['sale.inter.company.warning.wizard'].create({
                'wizard_id': self.id,
                'message': message
            })

            return {
                'name': _('Warning'),
                'type': 'ir.actions.act_window',
                'res_model': 'sale.inter.company.warning.wizard',
                'res_id': wizard.id,
                'view_mode': 'form',
                'target': 'new',
                'context': dict(self.env.context, active_id=self.id),
            }

        return None


    
    def action_confirm(self):
        result = self.check_available()
        if result:
            return result  # 👉 ต้อง return popup ถ้ามี warning
        if self.sale_id.type_id.inter_company_transactions:
            res_order = self.sale_id
        else:
            res_order = self.create_sale_order()
            self.sale_id.inter_so_company = res_order.name
        res_purchase = self.create_purchase_order(res_order)

        # for line in self.order_line:
        #     line.order_line.price_unit = line.price_unit

    #ของใหม่
    # def check_available(self):
    #     # if self.env.context.get('skip_pricelist_check'):
    #     #     return None

    #     # products_no_pricelist = set()

    #     for line in self.order_line:
    #         if line.product_id.type == "product":
    #             if self.inter_company_transactions:
    #                 res_product = line.product_id._compute_quantities_dict_company(
    #                     lot_id=None, owner_id=None, package_id=None,
    #                     # company_id=self.vendor_company_id
    #                     company_id = self.sale_id.company_id
    #                 )
    #             else:
    #                 res_product = line.product_id._compute_quantities_dict_company(
    #                     lot_id=None, owner_id=None, package_id=None,
    #                     company_id=self.inter_company_id
    #                 )
    #             free_qty = res_product[line.product_id.id]['free_qty']
    #             if free_qty < line.product_uom_qty:
    #                 raise UserError(_("%s ของไม่เพียงพอ" % line.product_id.name))

    #         pricelist_item = self.env["product.pricelist.item"].search([
    #             ("product_id", "=", line.product_id.id),
    #             ("pricelist_id", "=", self.pricelist_id.id)
    #         ])
    #         if not pricelist_item and not line.free_product:
    #             # products_no_pricelist.add(line.product_id.name)
    #             raise UserError(_("ไม่มีราคาซื้อขายระหว่างกัน กรุณาตรวจสอบใหม่อีกครั้ง \n %s " % line.product_id.name))


    #     if self.sale_type_check:
    #         for line in self.order_po_line:
    #             pricelist_item = self.env["product.pricelist.item"].search([
    #                 ("product_id", "=", line.product_id.id),
    #                 ("pricelist_id", "=", self.pricelist_id.id)
    #             ])
    #             if not pricelist_item and not line.free_product:
    #                 # products_no_pricelist.add(line.product_id.name)
    #                 raise UserError(_("ไม่มีราคาซื้อขายระหว่างกัน กรุณาตรวจสอบใหม่อีกครั้ง \n %s " % line.product_id.name))

    #     # if products_no_pricelist and not self.env.context.get('skip_pricelist_check'):
    #     #     message = _("ไม่มีราคาซื้อขายระหว่างกัน กรุณาตรวจสอบใหม่อีกครั้ง \n %s" % ", ".join(products_no_pricelist))
    #     #     wizard = self.env['sale.inter.company.warning.wizard'].create({
    #     #         'wizard_id': self.id,
    #     #         'message': message
    #     #     })

    #     #     return {
    #     #         'name': _('Warning'),
    #     #         'type': 'ir.actions.act_window',
    #     #         'res_model': 'sale.inter.company.warning.wizard',
    #     #         'res_id': wizard.id,
    #     #         'view_mode': 'form',
    #     #         'target': 'new',
    #     #         'context': dict(self.env.context, active_id=self.id),
    #     #     }

    #     return None


    
    # def action_confirm(self):
    #     self.check_available()
    #     # result = self.check_available()
    #     # if result:
    #     #     return result
    #     if self.sale_id.type_id.inter_company_transactions:
    #         res_order = self.sale_id
    #     else:
    #         res_order = self.create_sale_order()
    #         self.sale_id.inter_so_company = res_order.name
    #     res_purchase = self.create_purchase_order(res_order)

    #     # for line in self.order_line:
    #     #     line.order_line.price_unit = line.price_unit


    def _get_applicable_pricelist_item(self, product, quantity, pricelist):
        today = fields.Date.today()
        ProductPricelistItem = self.env["product.pricelist.item"]

        item = ProductPricelistItem.search([
            ("product_id", "=", product.id),
            ("pricelist_id", "=", pricelist.id),
            "|", ("date_start", "=", False), ("date_start", "<=", today),
            "|", ("date_end", "=", False), ("date_end", ">=", today),
            ("min_quantity", "<=", quantity),
        ], limit=1)

        if not item:
            item = ProductPricelistItem.search([
                ("product_tmpl_id", "=", product.product_tmpl_id.id),
                ("pricelist_id", "=", pricelist.id),
                "|", ("date_start", "=", False), ("date_start", "<=", today),
                "|", ("date_end", "=", False), ("date_end", ">=", today),
                ("min_quantity", "<=", quantity),
            ], limit=1)

        return item


    @api.onchange('order_po_line')
    def _onchange_price_unit_po(self):
        for line in self.order_po_line:
            line._change_price_unit()

    @api.onchange('order_line')
    def _onchange_price_unit_so(self):
        for line in self.order_line:
            line._change_price_unit()

class WizardSaleInterCompanyLine(models.TransientModel):
    _name = 'wizard.sale.inter.company.line'
    _description = 'wizard.sale.inter.company.line'

    wizard_sale_inter_company = fields.Many2one('wizard.sale.inter.company', string = 'Sale Inter Company')
    order_line = fields.Many2one('sale.order.line', string = 'Sale Order line')
    product_id = fields.Many2one(related='order_line.product_id', string = 'Product')
    categ_id = fields.Many2one(related='product_id.categ_id', string = 'Product Category' ,readonly=True)
    # free_qty = fields.Float(string='Available QTY',related="product_id.free_qty",digits=(16, 2))
    free_qty = fields.Float(string='Available QTY',readonly=True,digits=(16, 2))
    price_unit = fields.Float('Unit Price', digits = 'Product Price')
    price_unit_cus = fields.Float(related='order_line.price_unit',string="ราคาขายลูกค้า")
    product_uom_qty = fields.Float(related='order_line.product_uom_qty',string='Demand', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='UOM')
    order_qty = fields.Float(string='Order QTY', digits='Product Unit of Measure')
    triple_discount = fields.Char('Discount')
    unit_price_pricelist = fields.Float('Unit Price PriceList')
    free_product = fields.Boolean(string="Free")
    cost_price_list = fields.Float(string='Net Price')
    cost_price = fields.Float(string='Cost Price')

    def _change_price_unit(self):
        for line in self:
            wizard = line.wizard_sale_inter_company
            if not wizard:
                continue
            matched = False
            for po_line in wizard.order_po_line:
                if (po_line.product_id.id == line.product_id.id and
                    po_line.order_line.id == line.order_line.id):
                    po_line.price_unit = line.price_unit
                    matched = True

class WizardSaleInterCompanyLinePO(models.TransientModel):
    _name = 'wizard.sale.inter.company.line.po'
    _description = 'wizard.sale.inter.company.line.po'

    wizard_sale_inter_company = fields.Many2one('wizard.sale.inter.company', string = 'Sale Inter Company')
    order_line = fields.Many2one('sale.order.line', string = 'Sale Order line')
    product_id = fields.Many2one('product.product', string='Product')
    categ_id = fields.Many2one(related='product_id.categ_id', string = 'Product Category' ,readonly=True)
    # free_qty = fields.Float(string='Available QTY',related="product_id.free_qty",digits=(16, 2))
    free_qty = fields.Float(string='Available QTY',readonly=True,digits=(16, 2))
    price_unit = fields.Float(related='order_line.price_unit')
    product_uom_qty = fields.Float(related='order_line.product_uom_qty',string='Demand', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='UOM',related='product_id.uom_po_id')
    order_qty = fields.Float(string='Order QTY', digits='Product Unit of Measure')
    price_unit = fields.Float('Unit Price', required = True, digits = 'Product Price', default = 0.0)
    triple_discount = fields.Char('Discount')
    free_product = fields.Boolean(string="Free")
    cost_price_list = fields.Float(string='Cost Price List')

    def _change_price_unit(self):
        for line in self:
            wizard = line.wizard_sale_inter_company
            if not wizard:
                continue
            matched = False
            for so_line in wizard.order_line:
                if (so_line.product_id.id == line.product_id.id and
                    so_line.order_line.id == line.order_line.id):
                    so_line.price_unit = line.price_unit
                    matched = True