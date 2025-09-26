# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from lxml import etree
from datetime import datetime, timedelta, date
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import re


class QuotationBomLine(models.Model):
    _name = "quotation.bom.line"
    _description = "Components"


    order_id = fields.Many2one(
        "quotation.order",
        string="Order Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    origin_product_id = fields.Many2one(
        "product.product", string="Product", required=True, store=True
    )
    product_id = fields.Many2one(
        "product.product", string="Product Component", required=True, store=True
    )
    image_product = fields.Binary(
        "Image product", related="product_id.image_128", readonly=True
    )
    product_uom_qty = fields.Float(
        "Quantity.", digits="Product Unit of Measure", default=0.0
    )
    product_uom = fields.Many2one("uom.uom", "UoM")
    
class Quotations(models.Model):
    _name = 'quotation.order'
    _description = "Quotations Order"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'date_order desc, id desc'
    _check_company_auto = True

    order_bom_line = fields.One2many(
        "quotation.bom.line",
        "order_id",
        string="Components",
        compute="_compute_order_bom_line",
        store=True,
    )

    @api.depends("quotation_line.product_id", "quotation_line.product_uom_qty")
    def _compute_order_bom_line(self):
        for order in self:
            bom_lines = []
            for line in order.quotation_line:
                if not line.product_id:
                    continue
    
                bom = self.env['mrp.bom']._bom_find(product=line.product_id, company_id=order.company_id.id)
                
                if bom and bom.type == 'phantom':
                    for bom_line in bom.bom_line_ids:
                        bom_lines.append((0, 0, {
                            'origin_product_id': line.product_id.id,
                            'product_id': bom_line.product_id.id,
                            'product_uom_qty': bom_line.product_qty * line.product_uom_qty,
                            'product_uom': bom_line.product_uom_id.id,
                        }))
            
            order.order_bom_line = [(5, 0, 0)] + bom_lines

    is_below_cost = fields.Boolean(string="Is below cost", default=False)

    is_confirm_below_cost = fields.Boolean(
        string="Is confirm below cost", default=False, copy=False
    )

    is_approve_below_cost = fields.Boolean(
        string="Is approve below cost", default=False, copy=False
    )
    
    def action_confirm(self):
        # if not (self.type_id.inter_company_transactions or self.type_id.is_retail):
        #     if self.delivery_trl:
        #         if not self.delivery_trl_description:
        #             raise ValidationError(_("กรุณาระบุรายละเอียดของ สายส่ง TRL"))
        #     elif self.delivery_company:
        #         if not self.delivery_company_description:
        #             raise ValidationError(_("กรุณาระบุรายละเอียดของ Mode of Delivery"))
        #     else:
        #         raise ValidationError(_("กรุณาระบุสายส่ง TRL หรือ Mode of Delivery"))


        list_warning_below_cost = []
        
        for line in self.quotation_line:
            in_pricelist = self.env["product.pricelist.item"].search(
                            [
                                ("pricelist_id", "=", self.pricelist_id.id),
                                ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                            ], limit=1
                        )
            
            if not self.pricelist_id.approve_below_cost:
                if not self.type_id.below_cost:
                    if not line.product_id.product_tmpl_id.below_cost:
                        if line.product_id.product_tmpl_id.type != "service":

                            fixed_price = line.price_unit
                            cost_price = in_pricelist.pricelist_cost_price or line.product_id.product_tmpl_id.standard_price

                            if cost_price > fixed_price:
                                list_warning_below_cost.append({'product':line.product_id.name, 'price': fixed_price, 'cost': cost_price})

        # is_below_cost = True คือมีสินค้าต่ำกว่าทุนในการขาย ต้องแจ้งเตือน
        if list_warning_below_cost:
            if not self.is_confirm_below_cost: # for confirm from wizard
                return self.show_below_cost_warning_wizard(list_warning_below_cost)
            else:
                # return super(Quotations, self).action_confirm()
                self.state = 'approved'
        else:
            # return super(Quotations, self).action_confirm()
            self.state = 'approved'


    def show_below_cost_warning_wizard(self, list_warning_below_cost=[]):

        messages = []

        for list in list_warning_below_cost:

            line_message = f"{list['product']}, price: {list['price']}, cost: {list['cost']}"
            messages.append(line_message)

        message = "Your order has found selling price below cost. \n" + "\n".join(
            messages
        )

        return {
            "name": _("Below Cost Warning"),
            "type": "ir.actions.act_window",
            "res_model": "confirm.below.cost.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_quotation_order_id": self.id,
                "default_message": message,
            },
        }

    def approve_below_cost_wizard(self, list_warning_below_cost=[]):

        messages = []

        for list in list_warning_below_cost:

            line_message = f"{list['product']}, price: {list['price']}, cost: {list['cost']}"
            messages.append(line_message)

        message = "Your order has found selling price below cost. \n" + "\n".join(
            messages
        )

        return {
            "name": _("Below Cost Warning"),
            "type": "ir.actions.act_window",
            "res_model": "approve.below.cost.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_quotation_order_id": self.id,
                "default_message": message,
            },
        }

    def _default_validity_date(self):
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_quotation_validity_days'):
            days = self.env.company.quotation_validity_days
            if days > 0:
                return fields.Date.to_string(datetime.now() + timedelta(days))
        return False

    @api.model
    def _default_note(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'account.use_invoice_terms') and self.env.company.invoice_terms or ''

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    def _get_default_require_signature(self):
        return self.env.company.portal_confirmation_sign

    def _get_default_require_payment(self):
        return self.env.company.portal_confirmation_pay

    @api.model
    def _default_warehouse_id(self):
        # !!! Any change to the default value may have to be repercuted
        # on _init_column() below.
        return self.env.user._get_default_warehouse_id()

    @api.depends('global_discount','global_discount_update','quotation_line','quotation_line.product_id')
    def _compute_global_discount_total(self):
        for order in self:
            amount_untaxed = 0.0
            for line in order.quotation_line:
                if line.product_id != order.default_product_global_discount:
                    amount_untaxed += line.price_subtotal

            global_discount_total = 0.0
            if order.quotation_line:
                if order.global_discount:
                    try:
                        global_discount_discounts = order.global_discount.replace(" ", "").split("+")
                        pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                        for discount in global_discount_discounts:
                            if not pattern.match(discount):
                                raise ValidationError(_('Invalid Discount format : 20%+100'))

                        for discount in global_discount_discounts:
                            if discount.endswith("%"):
                                dis_percen = discount.replace("%", "")
                                discount_amount = ((amount_untaxed) * float(dis_percen)) / 100
                                amount_untaxed -= discount_amount
                                global_discount_total += discount_amount
                            else:
                                discount_amount = float(discount)
                                amount_untaxed -= discount_amount
                                global_discount_total += discount_amount
                    except:
                        raise ValidationError(_('Invalid Discount format : 20%+100'))
                    order.global_discount_total = global_discount_total
                    order.global_discount_update = global_discount_total
                else:
                    order.global_discount_total = 0.0

    @api.model
    def _default_global_discount(self):
        global_discount = self.env['ir.config_parameter'].sudo().get_param(
            'hdc_discount.global_discount_default_product_id')
        return global_discount if global_discount else False

    @api.depends('team_id')
    def _compute_member_ids(self):
        for rec in self:
            rec.member_ids = rec.team_id.member_ids.ids

    default_product_global_discount = fields.Many2one('product.product', default = _default_global_discount)

    name = fields.Char(string = 'Order Reference', required = True, copy = False, readonly = True,
                       states = {'draft': [('readonly', False)]}, index = True, default = lambda self: _('New'))
    origin = fields.Char(string = 'Source Document',
                         help = "Reference of the document that generated this sales order request.")
    client_order_ref = fields.Char(string = 'Customer Reference', copy = False)
    reference = fields.Char(string = 'Payment Ref.', copy = False,
                            help = 'The payment communication of this sale order.')
    state = fields.Selection(
        [('draft', 'Draft'), ('sent', 'Quotation Sent'),('approved', 'Approved'), ('sale', 'Sales Order'), ('done', 'Locked'),
            ('cancel', 'Cancelled'), ], string = 'Status', readonly = True, copy = False, index = True, tracking = 3,
        default = 'draft')
    date_order = fields.Datetime(string = 'Order Date', required = True, readonly = True, index = True,
                                 states = {'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy = False,
                                 default = fields.Datetime.now,
                                 help = "Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    validity_date = fields.Date(string = 'Expiration', readonly = True, copy = False,
                                states = {'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                default = _default_validity_date)
    require_signature = fields.Boolean('Online Signature', default = _get_default_require_signature, readonly = True,
                                       states = {'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                       help = 'Request a online signature to the customer in order to confirm orders automatically.')
    require_payment = fields.Boolean('Online Payment', default = _get_default_require_payment, readonly = True,
                                     states = {'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                     help = 'Request an online payment to the customer in order to confirm orders automatically.')

    partner_id = fields.Many2one('res.partner', string = 'Customer', readonly = True,
        states = {'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required = True,
        change_default = True, index = True, tracking = 1,
        domain = "['|', ('company_id', '=', False), ('company_id', '=', company_id), ('parent_id', '=', False)]")
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Account', readonly=True, required=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    pricelist_id = fields.Many2one('product.pricelist', string = 'Pricelist', check_company = True,
        # Unrequired company
        required = True, readonly = True, states = {'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain = "['|', ('company_id', '=', False), ('company_id', '=', company_id),('id','in',pricelist_ids)]",
        tracking = 1, help = "If you change the pricelist, only newly added lines will be affected.")

    currency_id = fields.Many2one('res.currency', store = True,domain = [('rate_type','=', 'buy')])

    quotation_line = fields.One2many('quotation.order.line', 'quotation_id', string = 'Quotation Lines',
                                 states = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy = True,
                                 auto_join = True)

    note = fields.Text('Terms and conditions', default=_default_note)

    amount_untaxed = fields.Monetary(string = 'Untaxed Amount', store = True, readonly = True, compute = '_amount_all',
                                     tracking = 5)
    amount_tax = fields.Monetary(string = 'Taxes', store = True, readonly = True, compute = '_amount_all')
    amount_total = fields.Monetary(string = 'Total', store = True, readonly = True, compute = '_amount_all',
                                   tracking = 4)
    payment_term_id = fields.Many2one('account.payment.term', string = 'Payment Terms', check_company = True,
        # Unrequired company
        domain = "['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    fiscal_position_id = fields.Many2one('account.fiscal.position', string = 'Fiscal Position',
        domain = "[('company_id', '=', company_id)]", check_company = True,
        help = "Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices."
               "The default value comes from the customer.")
    company_id = fields.Many2one('res.company', 'Company', required = True, index = True,
                                 default = lambda self: self.env.company)
    team_id = fields.Many2one('crm.team', 'Sales Team', 
                            #   change_default = True, 
                            #   default = _get_default_team
                            )

    signature = fields.Image('Signature', help = 'Signature received through the portal.', copy = False,
                             attachment = True, max_width = 1024, max_height = 1024)
    signed_by = fields.Char('Signed By', help = 'Name of the person that signed the SO.', copy = False)
    signed_on = fields.Datetime('Signed On', help = 'Date of the signature.', copy = False)

    commitment_date = fields.Datetime('Delivery Date', copy = False,
                                      states = {'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                      help = "This is the delivery date promised to the customer. "
                                             "If set, the delivery order will be scheduled based on "
                                             "this date rather than product lead times.")

    show_update_pricelist = fields.Boolean(string = 'Has Pricelist Changed',
                                           help = "Technical Field, True if the pricelist was changed;\n"
                                                  " this will then display a recomputation button")
    customer_po = fields.Char(string = "",copy=False)
    sub_discount_amount = fields.Float(string = "Sub Discount Amount", compute = '_compute_sub_discount_amount')
    sub_discount_percentage = fields.Float(string = "Sub Disc%", compute = '_compute_sub_discount_amount')

    total_discount_amount = fields.Float(string = "Total Discount%", compute = '_compute_total_discount')
    total_discount_percentage = fields.Float(string = "Total Discount Percentage", compute = '_compute_total_discount')

    total_discount = fields.Float(string = "Total Discount")
    amount_before_discount = fields.Float(string = "Amount Before Discount",
                                          compute = '_compute_amount_before_discount')

    global_discount = fields.Char(string = "Global Discount")
    global_discount_update = fields.Char()
    global_discount_total = fields.Float(string = "Global Discount Total", compute = '_compute_global_discount_total',
                                         store = True)

    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High'), ('3', 'Urgent')], 'Priority',
                                default = '0', index = True)

    delivery_time = fields.Many2one('delivery.time', string = 'Delivery Time', tracking = True)

    delivery_terms = fields.Many2one('account.incoterms', string = 'Delivery Terms', tracking = True)

    offer_validation = fields.Many2one('offer.validation', string = 'Offer Validation', tracking = True)

    sale_spec = fields.Many2one('res.users', string = 'Sale Spec')
    user_sale_agreement = fields.Many2one('res.users', string = 'Administrator', default = lambda self: self.env.user)

    # member_ids = fields.One2many('res.users', 'team_id', related = "team_id.member_ids", store = True)
    member_ids = fields.Many2many('res.users', compute = "_compute_member_ids")
    user_id = fields.Many2one('res.users', string = 'Salesperson', index = True, tracking = 2,
                              default = lambda self: self.env.user, domain = lambda
            self: "[('id', 'in', member_ids),('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
            self.env.ref("sales_team.group_sale_salesman").id), )
    sale_manager_id = fields.Many2one("res.users", string = "Sale Manager")
    modify_type_txt = fields.Char(string = "แปลง/Type/Block")
    plan_home = fields.Char(string = "แบบบ้าน")
    room = fields.Char(string = "ชั้นห้อง")
    requested_ship_date = fields.Date(string = "Requested ship date")
    requested_receipt_date = fields.Date(string = "Requested receipt date",default=fields.Date.context_today)
    confirm_date = fields.Date(string = "Confirm Date",default=fields.Date.context_today)
    delivery_trl = fields.Many2one("delivery.round", string = "สายส่ง TRL")
    delivery_trl_description = fields.Char(related = "delivery_trl.name", string = "สายส่ง TRL Description")
    po_date = fields.Date(string = "PO Date")
    expire_date = fields.Date(string = "Expire Date PO")
    customer_contact_date = fields.Char(string = "Customer Contact No.")
    delivery_company = fields.Many2one("company.delivery.round", string = "Mode of delivery")
    delivery_company_description = fields.Char(related = "delivery_company.name",
                                               string = "Mode of delivery Description")
    remark = fields.Char(string = "Remark")
    type_id = fields.Many2one(
        comodel_name="sale.order.type",
        string="Sale Type",
        compute="_compute_sale_type_id",
        store=True,
        readonly=True,
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        # domain="[('id', 'in', sale_type_ids)]",
        ondelete="restrict",
        copy=True,
    )
    inter_company_transactions = fields.Boolean(related = "type_id.inter_company_transactions")
    sale_type_ids = fields.Many2many(related="team_id.sale_type_ids")
    billing_period_id = fields.Many2one(comodel_name='account.billing.period', string="Billing Period")
    billing_route_id = fields.Many2one(comodel_name='account.billing.route', string="Billing Route")
    project_name = fields.Many2one("sale.project",string = "Project Name",domain="['|',('status', '=', 'active'),('end_date', '<', date_order), ('end_date', '=', False)]")
    remark_project = fields.Text('Remark ข้อมูลโครงการ')
    blanket_order_id = fields.Many2one("sale.blanket.order", string = "Project Name")
    contact_person = fields.Many2one('res.partner', string = 'Contact Person', readonly = False)
    warehouse_id = fields.Many2one('stock.warehouse', string = 'Warehouse', required = True, readonly = True,
        states = {'draft': [('readonly', False)], 'sent': [('readonly', False)]}, default = _default_warehouse_id,
        check_company = True)
    pricelist_ids = fields.One2many('product.pricelist', compute = '_compute_pricelist_ids')
    quotation_line_detail = fields.One2many('quotation.order.line', 'quotation_id', string = 'Quotation Lines Detail', copy = False,
                                        auto_join = True)

    sale_count = fields.Integer(compute = "_compute_sale_count")
    days_delivery = fields.Char(string="Days Delivery")
    payment_method_id = fields.Many2one('account.payment.method', string = 'Payment Method')

    branch_id = fields.Many2one('res.branch', string='Branch')
    tag_ids = fields.Many2many('crm.tag', string='Tags')
    outline_agreement = fields.Char(string="Outline Agreement")

    lang_code = fields.Char(string='Language Code', compute='_compute_lang_code', store=True)

    @api.depends('partner_id.lang')
    def _compute_lang_code(self):
        for order in self:
            order.lang_code = order.partner_id.lang

    @api.onchange('project_name')
    def _onchange_project_name(self):
        if self.project_name and self.project_name.remark_project:
            self.remark_project = self.project_name.remark_project
        else:
            self.remark_project = False

    @api.model
    def _default_note_en(self):
        remark_text = self.env['ir.config_parameter'].sudo().get_param('hdc_sale_remark.remark_text_en')
        return remark_text if remark_text else ''
    
    @api.model
    def _default_note_th(self):
        remark_text = self.env['ir.config_parameter'].sudo().get_param('hdc_sale_remark.remark_text_th')
        return remark_text if remark_text else ''
    
    note_th = fields.Text('Terms and conditions', default=_default_note_th)
    note_en = fields.Text('Terms and conditions', default=_default_note_en)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Quotations, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            form_view = self.env.ref('hdc_quotation_order.view_quotation_order_form')
            arch_tree = etree.fromstring(form_view.arch)
            if not self.env.user.has_group('sales_team.group_sale_manager'):
                for node in arch_tree.xpath("//field[@name='payment_method_id']"):
                    node.set('readonly', '1')
            else:
                for node in arch_tree.xpath("//field[@name='payment_method_id']"):
                    node.set('readonly', '0')
            form_view.sudo().write({'arch': etree.tostring(arch_tree, encoding='unicode')})
        return res

    @api.onchange("partner_id", "team_id")
    def onchange_partner_id_team_id(self):
        customer_credit_id = self.env["customer.credit.limit"].search([('partner_id', '=', self.partner_id.id)])
        if customer_credit_id:
            customer = customer_credit_id.credit_id.credit_line.filtered(lambda l: l.sale_team_id == self.team_id)
            if customer:
                self.payment_term_id = customer.payment_term_id.id
                self.payment_method_id = customer.payment_method_id.id
                self.billing_period_id = customer.billing_period_id.id
            else:
                self.payment_term_id = False
                self.payment_method_id = False
                self.billing_period_id = False
        else:
            self.payment_term_id = self.partner_id.property_payment_term_id.id
            self.payment_method_id = False
            self.billing_period_id = self.partner_id.billing_period_id.id

    def action_approved(self):

        list_warning_below_cost = []

        for line in self.quotation_line:            

            in_pricelist = self.env["product.pricelist.item"].search(
                            [
                                ("pricelist_id", "=", self.pricelist_id.id),
                                ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                            ], limit=1
                        )
                    
            if line.product_id.product_tmpl_id.type != "service":

                fixed_price = line.price_unit
                cost_price = in_pricelist.pricelist_cost_price or line.product_id.product_tmpl_id.standard_price

                if cost_price > fixed_price:
                        
                    if in_pricelist:
                        if not self.pricelist_id.approve_below_cost:
                            list_warning_below_cost.append({'product':line.product_id.name, 'price': fixed_price, 'cost': cost_price})
                    else:
                        if line.product_id.product_tmpl_id.below_cost or self.type_id.below_cost:
                            list_warning_below_cost.append({'product':line.product_id.name, 'price': fixed_price, 'cost': cost_price})

        # is_below_cost = True คือมีสินค้าต่ำกว่าทุนในการขาย ต้องแจ้งเตือน
        if self.requested_receipt_date:
            self.requested_receipt_date += timedelta(days=4)
        
        if not self.confirm_date:
            self.confirm_date = fields.Date.today()

        if list_warning_below_cost:
            if not self.is_approve_below_cost:                
                return self.approve_below_cost_wizard(list_warning_below_cost)
            else:
                attachment_id = self.env['ir.attachment'].search([('res_model', '=', 'quotation.order'),('res_id', '=', self.id)])
                # if not attachment_id:
                #     raise ValidationError(_("กรุณาแนบเอกสารอนุมัติของผู้จัดการ"))
                self.state = 'sale'
        else:
            attachment_id = self.env['ir.attachment'].search([('res_model', '=', 'quotation.order'),('res_id', '=', self.id)])
            # if not attachment_id:
            #     raise ValidationError(_("กรุณาแนบเอกสารอนุมัติของผู้จัดการ"))
            self.state = 'sale'

    def action_lock(self):
        self.state = 'done'

    def action_unlock(self):
        self.state = 'sale'

    def action_set_to_draft(self):
        self.is_confirm_below_cost = False
        self.is_approve_below_cost = False
        self.state = 'draft'

    def action_cancel(self):
        self.state = 'cancel'

    def _compute_sale_count(self):
        for rec in self:
            sale_id = self.env['sale.order'].search([('quotation_id', '=', rec.id)])
            rec.sale_count = len(sale_id)

    def action_view_sale_orders(self):
        self.ensure_one()
        action = {
            "name": _("Orders"),
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "target": "current",
            }
        sale_id = self.env['sale.order'].search([('quotation_id', '=', self.id)])
        view = self.env.ref("sale.view_order_form")
        if len(sale_id.ids) == 1:
            action["res_id"] = sale_id.id
            action["view_mode"] = "form"
            action["views"] = [(view.id, "form")]
        else:
            action["view_mode"] = "tree,form"
            action["domain"] = [("id", "in", sale_id.ids)]
        return action

    def open_wizard_create_sale_order(self):
        line_ids = []
        if self.quotation_line:
            for line in self.quotation_line:
                if line.is_global_discount == False:
                    line_ids.append((0, 0, {
                        'quotation_line': line.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'price_unit': line.price_unit,
                        'display_type': line.display_type,
                        'name': line.name,
                        "external_customer": line.external_customer.id if line.external_customer else False,
                        "external_item": line.external_item,
                        "barcode_customer": line.barcode_customer,
                        "barcode_modern_trade": line.barcode_modern_trade,
                        "description_customer": line.description_customer,
                        "modify_type_txt": line.modify_type_txt,
                        "plan_home": line.plan_home,
                        "room": line.room,
                        }))
        wizard = self.env["wizard.create.sale.order"].create({
            "quotation_id": self.id,
            "order_line": line_ids
            })
        action = {
            'name': 'Create Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.create.sale.order',
            'res_id': wizard.id,
            'view_mode': 'form',
            "target": "new",
            }
        return action

    def create_sale_order(self):
        quotation_line = []
        for line in self.quotation_line:
            quotation_line.append((0,0, {
                        'name': line.name,
                        'price_unit': line.price_unit,
                        'tax_id': line.tax_id.ids,
                        'product_id': line.product_id.id,
                        'product_template_id': line.product_template_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'product_uom_category_id': line.product_uom_category_id.id,
                        'product_no_variant_attribute_value_ids': line.product_no_variant_attribute_value_ids.ids,
                        'display_type': line.display_type,
                        'triple_discount': line.triple_discount,
                        'rounding_price': line.rounding_price,
                        'is_global_discount': line.is_global_discount
                        }))
        
        if self.confirm_date:
            new_date = self.confirm_date + timedelta(days=3)

        quotation = {
            'order_line': quotation_line,
            'quotation_id': self.id,
            'default_product_global_discount': self.default_product_global_discount.id,
            'origin': self.origin,
            'client_order_ref': self.client_order_ref,
            'reference': self.reference,
            'date_order': self.date_order,
            'validity_date': self.validity_date,
            'require_signature': self.require_signature,
            'require_payment': self.require_payment,
            'partner_id': self.partner_id.id,
            'partner_invoice_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'pricelist_id': self.pricelist_id.id,
            'currency_id': self.currency_id.id,
            'note': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
            'company_id': self.company_id.id,
            'team_id': self.team_id.id,
            'signature': self.signature,
            'signed_by': self.signed_by,
            'signed_on': self.signed_on,
            'commitment_date': self.commitment_date,
            'show_update_pricelist': self.show_update_pricelist,
            'customer_po': self.customer_po,
            'total_discount': self.total_discount,
            'global_discount': self.global_discount,
            'global_discount_update': self.global_discount_update,
            'priority': self.priority,
            'delivery_time': self.delivery_time.id,
            'delivery_terms': self.delivery_terms.id,
            'offer_validation': self.offer_validation.id,
            'sale_spec': self.sale_spec.id,
            'user_sale_agreement': self.user_sale_agreement.id,
            'user_id': self.user_id.id,
            'sale_manager_id': self.sale_manager_id.id,
            'modify_type_txt': self.modify_type_txt,
            'plan_home': self.plan_home,
            'requested_ship_date': self.requested_ship_date,
            'requested_receipt_date': self.requested_receipt_date,
            'delivery_trl': self.delivery_trl.id,
            'customer_contact_date': new_date if new_date else self.customer_contact_date,
            'delivery_company': self.delivery_company.id,
            'remark': self.remark,
            'type_id': self.type_id.id,
            'billing_period_id': self.billing_period_id.id,
            'billing_route_id': self.billing_route_id.id,
            'blanket_order_id': self.blanket_order_id.id,
            'contact_person': self.contact_person.id,
            'warehouse_id': self.warehouse_id.id,
            'branch_id': self.branch_id.id,
            }
        sale_id = self.env['sale.order'].create(quotation)
        action = {
            'name': 'Sales Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_id.id,
            'view_mode': 'form',
            }
        return action

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            qo_type = self.env["sale.order.type"].browse(vals["type_id"])
            if qo_type.qo_sequence_id:
                vals["name"] = qo_type.qo_sequence_id.next_by_id() or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('quotation.order') or _('New')
        return super(Quotations, self).create(vals)

    @api.depends('partner_id', 'user_id', 'type_id')
    def _compute_pricelist_ids(self):
        for order in self:
            all_pricelists = self.env['product.pricelist'].browse([])
            partner = order.partner_id

            # Master Pricelist
            domain_master_pricelist = [
                ('is_default', '=', True),
                ('partner_id', '=', order.partner_id.id)
            ]
            pricelists_master = self.env['product.pricelist.customer'].search(domain_master_pricelist)
            if pricelists_master:
                all_pricelists |= pricelists_master.mapped('pricelist_id')

            # Master Customer
            if partner.parent_id:
                partner = partner.parent_id

            if partner.pricelist_ids:
                all_pricelists |= partner.pricelist_ids

            elif partner.property_product_pricelist:
                all_pricelists |= partner.property_product_pricelist

            # Pricelist All
            if not all_pricelists:
                pricelist_all = self.env['product.pricelist'].search([('pricelist_all', '=', True)])
                all_pricelists |= pricelist_all

            # Sale Type
            if order.type_id and order.type_id.pricelist_id:
                pricelist_from_sale_type = order.type_id.pricelist_id
                exists = self.env['product.pricelist.customer'].search_count([
                    ('partner_id', '=', order.partner_id.id),
                    ('pricelist_id', '=', pricelist_from_sale_type.id)
                ])
                if exists:
                    all_pricelists |= pricelist_from_sale_type

            order.pricelist_ids = all_pricelists
            # order.pricelist_id = all_pricelists[0].id if all_pricelists else False
    
    @api.onchange('partner_id', 'user_id', 'type_id')
    def _onchange_pricelist_id(self):
        for order in self:
            all_pricelists = self.env['product.pricelist'].browse([])
            partner = order.partner_id

            # Master Pricelist
            domain_master_pricelist = [
                ('is_default', '=', True),
                ('partner_id', '=', order.partner_id.id)
            ]
            pricelists_master = self.env['product.pricelist.customer'].search(domain_master_pricelist)
            if pricelists_master:
                all_pricelists |= pricelists_master.mapped('pricelist_id')

            # Master Customer
            if partner.parent_id:
                partner = partner.parent_id

            if partner.pricelist_ids:
                all_pricelists |= partner.pricelist_ids

            elif partner.property_product_pricelist:
                all_pricelists |= partner.property_product_pricelist

            # Pricelist All
            if not all_pricelists:
                pricelist_all = self.env['product.pricelist'].search([('pricelist_all', '=', True)])
                all_pricelists |= pricelist_all

            # Sale Type
            if order.type_id and order.type_id.pricelist_id:
                pricelist_from_sale_type = order.type_id.pricelist_id
                exists = self.env['product.pricelist.customer'].search_count([
                    ('partner_id', '=', order.partner_id.id),
                    ('pricelist_id', '=', pricelist_from_sale_type.id)
                ])
                if exists:
                    all_pricelists |= pricelist_from_sale_type

            order.pricelist_id = all_pricelists[0].id if all_pricelists else False

    @api.onchange('pricelist_id')
    def _onchange_pricelist_to_change_fiscal_position_id(self):
        self.currency_id = self.pricelist_id.currency_id.id
        if self.quotation_line and self.pricelist_id and self._origin.pricelist_id != self.pricelist_id:
            self.show_update_pricelist = True
        else:
            self.show_update_pricelist = False
        for order in self:
            fiscal_position_id = order.pricelist_id.fiscal_position_id
            if fiscal_position_id:
                order.fiscal_position_id = fiscal_position_id


    def default_get(self, fields_list):
        defaults = super(Quotations, self).default_get(fields_list)
        team_id = defaults.get('team_id')
        team = self.env['crm.team'].search([('id', '=', team_id)])
        defaults['sale_manager_id'] = team.user_id.id
        return defaults

    @api.depends("partner_id", "company_id")
    def _compute_sale_type_id(self):
        for record in self:
            if not record.partner_id:
                record.type_id = False
            else:
                sale_type = (
                    record.partner_id.with_company(record.company_id).sale_type
                    or record.partner_id.commercial_partner_id.with_company(
                        record.company_id
                    ).sale_type
                )
                if sale_type:
                    record.type_id = sale_type

    # @api.onchange("team_id")
    # def _domain_type_id(self):
    #     if self.team_id:
    #         return {
    #             "domain": {"type_id": [("id", "in", self.team_id.sale_type_ids.ids), ("company_id", "=", self.company_id.id)]}
    #         }
    #     else:
    #         return {"domain": {"type_id": []}}
    
    @api.onchange('type_id')
    def _onchange_sale_type(self):
        for order in self:
            # if order.type_id and order.type_id.pricelist_id:
            #     order.pricelist_id = order.type_id.pricelist_id
            if order.type_id.branch_id:
                order.branch_id = order.type_id.branch_id

    @api.constrains('price_total')
    def _check_amount_total(self):
        for line in self:
            if line.price_total < 0 :
                raise UserError('Total is negative. Please check.')
            
    @api.onchange('fiscal_position_id')
    def _compute_tax_id(self):
        """
        Trigger the recompute of the taxes if the fiscal position is changed on the SO.
        """
        for order in self:
            order.quotation_line._compute_tax_id()

    def write(self, vals):
        global_discount_id = self.env['ir.config_parameter'].sudo().get_param('hdc_discount.global_discount_default_product_id')
        global_discount = self.env["product.product"].search([("id", "=", global_discount_id)],limit=1)
        global_discount_product = global_discount if global_discount else False

        if 'global_discount_update' in vals:
            if global_discount_product:
                old_lines = self.mapped("quotation_line")
                check_global_discount_line = []
                for line in old_lines:
                    if line.product_id == global_discount_product:
                        check_global_discount_line.append(line.id)
                        line.write({'price_unit': -float(vals.get("global_discount_update"))})

        if 'quotation_line' in vals:
            if global_discount_product:
                old_lines = self.mapped("quotation_line")
                check_global_discount_line = []
                for line in old_lines:
                    if line.product_id == global_discount_product:
                        check_global_discount_line.append(line.id)
                        line.write({'price_unit': -self.global_discount_total})
        
        if 'global_discount' in vals:
            if vals.get('global_discount'):
                gdt_line = self._global_discount_total_line(vals['global_discount'])

                if global_discount_product:
                    old_lines = self.mapped("quotation_line")
                    check_global_discount_line = []
                    for line in old_lines:
                        if line.product_id == global_discount_product:
                            check_global_discount_line.append(line.id)
                            line.write({'price_unit': -gdt_line})
                    company_id = self.env.company.id
                    taxes_ids = global_discount_product.taxes_id.filtered(lambda tax: tax.company_id.id == company_id).ids
                    
                    if not check_global_discount_line:
                        description = global_discount_product.description_sale if global_discount_product.description_sale else "-"
                        quotation_line_values = {
                            'quotation_id': self.id,
                            'product_id': global_discount_product.id,
                            'name': description,
                            'product_uom_qty': 1,
                            'product_uom': global_discount_product.uom_id.id,
                            'price_unit': -gdt_line,
                            'is_global_discount': True,
                            'tax_id': [(6, 0, taxes_ids)] if taxes_ids else False
                        }
                        quotation_line = self.env['quotation.order.line'].create(quotation_line_values)
                        if quotation_line:
                            quotation_line.sequence = self.max_line_sequence
                            quotation_line.sequence2 = self.max_line_sequence + 1
            self._compute_tax_id()
        self._reset_sequence()

        # โค็ดสำหรับลบ line global_discount_line กรณีที่ มันโดนลบออกจาก sale order line
        if 'quotation_line' in vals:
            for line in vals['quotation_line']:
                if line[0] == 2:
                    global_discount_product = self.default_product_global_discount
                    check_global_discount_line = self.env["quotation.order.line"].search([('id', '=', line[1])], limit = 1)

                    if check_global_discount_line.product_id == global_discount_product:
                        self.global_discount = 0

        if vals.get("type_id"):
            qo_type = self.env["sale.order.type"].browse(vals["type_id"])
            if qo_type.sequence_id:
                for record in self:
                    if (
                        record.state in {"draft", "sent"}
                        and record.type_id.sequence_id != qo_type.sequence_id
                    ):
                        new_vals = vals.copy()
                        # new_vals["name"] = qo_type.sequence_id.next_by_id(
                        #     sequence_date=vals.get("date_order")
                        # )
                        if qo_type.qo_sequence_id:
                            vals["name"] = qo_type.qo_sequence_id.next_by_id() or _('New')
                        else:
                            vals['name'] = self.env['ir.sequence'].next_by_code('quotation.order') or _('New')
                        super(Quotations, record).write(new_vals)
                    else:
                        super(Quotations, record).write(vals)
                return True
        res = super().write(vals)
        return res

    @api.onchange('quotation_line', 'quotation_line.price_total')
    def _compute_amount_before_discount(self):
        for order in self:
            amount_untaxed = sum(line.price_total for line in order.quotation_line if not line.is_global_discount)
            order.amount_before_discount = amount_untaxed

    def _global_discount_total_line(self, gb):
        for order in self:
            amount_untaxed = 0.0
            for line in order.quotation_line:
                if line.product_id != order.default_product_global_discount:
                    amount_untaxed += line.price_subtotal

            global_discount_total = 0.0

            if gb:
                try:

                    global_discount_discounts = gb.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                    for discount in global_discount_discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for discount in global_discount_discounts:
                        if discount.endswith("%"):
                            dis_percen = discount.replace("%", "")
                            discount_amount = ((amount_untaxed)*float(dis_percen))/100
                            amount_untaxed -= discount_amount
                            global_discount_total += discount_amount
                        else:
                            discount_amount = float(discount)
                            amount_untaxed -= discount_amount
                            global_discount_total += discount_amount
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))

                return global_discount_total

    @api.constrains('customer_po')
    def _check_customer_po_unique(self):
        for order in self:
            if order.customer_po:
                domain = [('customer_po', '=', order.customer_po), ('partner_id', '=', order.partner_id.id),
                    ('id', '!=', order.id),  # Exclude the current order
                    ]
                duplicate_orders = self.search(domain)
                if duplicate_orders:
                    raise ValidationError("Customer PO No must be unique.")

    @api.onchange('quotation_line', 'quotation_line.price_unit', 'quotation_line.price_subtotal', 'quotation_line.triple_discount',
                  'global_discount', 'global_discount_total', 'write_date', 'quotation_line.product_uom_qty')
    def _compute_sub_discount_amount(self):
        for order in self:
            sub_discount = 0.0
            percen_discount = 0.0
            total_std_price = 0.0
            total_subtotal = 0.0
            for line in order.quotation_line:
                if line.product_id and line.product_id.lst_price > 0 and line.product_uom_qty > 0:
                    std_price = line.product_id.lst_price
                    if line.product_id.uom_id:
                        new_qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
                    else:
                        new_qty = line.product_uom_qty
                    # หาผลรวมของ public price * product uom qty * factor
                    # total_std_price += std_price * line.product_uom_qty * ratio
                    total_std_price += std_price*new_qty

                    # หา price subtotal
                    total_subtotal += line.price_total  # total_subtotal += line.price_subtotal

            sub_discount = total_std_price - total_subtotal
            if total_std_price != 0:
                percen_discount = ((total_std_price - total_subtotal)*100/total_std_price)

            if sub_discount < 0 or percen_discount < 0:
                order.sub_discount_amount = 0.0
                order.sub_discount_percentage = 0.0
            else:
                order.sub_discount_amount = sub_discount
                order.sub_discount_percentage = percen_discount

    @api.onchange('quotation_line', 'quotation_line.price_unit', 'quotation_line.price_subtotal', 'quotation_line.triple_discount',
                  'global_discount', 'global_discount_total', 'write_date', 'quotation_line.product_uom_qty')
    def _compute_total_discount(self):
        for order in self:
            total_discount = 0.0
            total_percen_discount = 0.0
            total_std_price = 0.0
            total_subtotal = 0.0
            
            for line in order.quotation_line:
                if line.product_id and line.product_id.lst_price > 0 and line.product_uom_qty > 0:
                    std_price = line.product_id.lst_price
                    line_price_subtotal = line.price_subtotal
                    line_sub_discount = order.sub_discount_amount
                    
                    if line.product_id.uom_id:
                        new_qty = line.product_uom._compute_quantity(
                            line.product_uom_qty, line.product_id.uom_id
                        )
                    else:
                        new_qty = line.product_uom_qty
 
                    #หาผลรวมของ public price * product uom qty * factor
                    total_std_price += std_price * new_qty
                    # total_std_price += std_price * line.product_uom_qty * ratio
                    
                    #หา price subtotal
                    total_subtotal += line.price_total
                    # total_subtotal += line.price_subtotal

            total_discount = (((total_std_price) - (total_subtotal) + order.global_discount_total))
            
            if total_std_price != 0:
                total_percen_discount = (((total_std_price) - (total_subtotal) + order.global_discount_total) * 100 / total_std_price)
            
            if total_discount < 0 or total_percen_discount < 0:
                order.total_discount_amount = 0.0
                order.total_discount_percentage = 0.0
            else:
                order.total_discount_amount = total_discount
                order.total_discount_percentage = total_percen_discount 
            order.total_discount_amount_new = order.global_discount_total

    @api.depends('global_discount','global_discount_update','quotation_line','quotation_line.product_id')
    def _compute_global_discount_total(self):
        for order in self:
            global_discount_total = 0.0
            order._compute_amount_before_discount()
            if order.global_discount:
                try:
                    global_discount_discounts = order.global_discount.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                    for discount in global_discount_discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for discount in global_discount_discounts:
                        if discount.endswith("%"):
                            dis_percen = discount.replace("%", "")
                            discount_amount = ((order.amount_before_discount) * float(dis_percen)) / 100
                            global_discount_total += discount_amount
                        else:
                            discount_amount = float(discount)
                            global_discount_total += discount_amount
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))
                order.global_discount_total = global_discount_total
                order.global_discount_update = global_discount_total
            else:
                order.global_discount_total = 0.0

    @api.depends('quotation_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.quotation_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    def update_prices(self):
        self.ensure_one()
        for line in self._get_update_prices_lines():
            line.product_uom_change()
            line.discount = 0  # Force 0 as discount for the cases when _onchange_discount directly returns
            line._onchange_discount()
        self.show_update_pricelist = False
        self.message_post(body=_("Product prices have been recomputed according to pricelist <b>%s<b> ", self.pricelist_id.display_name))


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        - Sales Team
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False
            })
            return

        self = self.with_company(self.company_id)

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            # 'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.context.get('default_user_id', self.env.uid)
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            values['team_id'] = self.env['crm.team'].with_context(
                default_team_id=self.partner_id.team_id.id
            )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)], user_id=user_id)
        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id
        self.update(values)

    def print(self):
        self.ensure_one()
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.quotation.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.state,
                            "default_quotation_id": self.id,
                            },

            }
    
    def check_iso_name(self, check_iso):
        for sale in self:
            check_model = self.env["ir.actions.report"].search([('model', '=', 'quotation.order'),('report_name', '=', check_iso)], limit=1)
            if check_model:
                return check_model.iso_name
            else:
                return "-"
            
    @api.onchange('fiscal_position_id')
    def _onchange_fiscal_position_id(self):
        for line in self.quotation_line:
            fpos = self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda t: t.company_id == line.env.company)
            line.tax_id = fpos.map_tax(taxes, line.product_id, self.partner_shipping_id)

    @api.depends("quotation_line")
    def _compute_max_line_sequence(self):
        """Allow to know the highest sequence entered in sale order lines.
        Then we add 1 to this value for the next sequence.
        This value is given to the context of the o2m field in the view.
        So when we create new sale order lines, the sequence is automatically
        added as :  max_sequence + 1
        """
        for sale in self:
            sale.max_line_sequence = max(sale.mapped("quotation_line.sequence") or [0]) + 1

    max_line_sequence = fields.Integer(
        string="Max sequence in lines", compute="_compute_max_line_sequence", store=True
    )
    total_discount_amount_new = fields.Float(string="Total Discount", compute='_compute_total_discount')

    def _reset_sequence(self):
        for order in self:
            current_sequence = 1
            max_sequence = 0
            global_discount_line = None

            for line in sorted(order.quotation_line, key=lambda x: (x.sequence, x.id)):
                if line.product_id == order.env["product.product"].search([('name', '=', "Global Discount"), ('type', '=', "service")], limit=1):
                    #โค็ดสำหรับดักเคสกรณี global_discount seq
                    global_discount_line = line
                    continue  

                if line.sequence2 != current_sequence:
                    line.sequence2 = current_sequence

                if not line.display_type:
                    current_sequence += 1

                max_sequence = max(max_sequence, line.sequence2)

            if global_discount_line:
                global_discount_line.sequence = order.max_line_sequence
                global_discount_line.sequence2 = max_sequence + 1

    def copy(self, default=None):
        return super(Quotations, self.with_context(keep_line_sequence=True)).copy(
            default
        )

    rounding_untax = fields.Char(string='Rounding Untaxed Amount')
    rounding_taxes = fields.Char(string='Rounding Taxes')
    rounding_total = fields.Char(string='Rounding Total')

    def action_rounding_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Total Rounding',
            'view_mode': 'form',
            'res_model': 'wizard.quotation.change.total',
            'target': 'new',
            'context': {
                'default_quotation_id': self.id,
                'default_rounding_untax': self.rounding_untax,
                'default_rounding_taxes': self.rounding_taxes,
                'default_rounding_total': self.rounding_total,
            },
        }
    
    def recalculate_global_discount(self):
        return True
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Quotations, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            form_view = self.env.ref('hdc_quotation_order.view_quotation_order_form')
            arch_tree = etree.fromstring(form_view.arch)
            if not self.env.user.has_group('sales_team.group_sale_manager'):
                for node in arch_tree.xpath("//field[@name='payment_method_id']"):
                    node.set('readonly', '1')
                for node1 in arch_tree.xpath("//field[@name='payment_term_id']"):
                    node1.set('readonly', '1')
                for node2 in arch_tree.xpath("//field[@name='billing_period_id']"):
                    node2.set('readonly', '1')
            else:
                for node in arch_tree.xpath("//field[@name='payment_method_id']"):
                    node.set('readonly', '0')
                for node1 in arch_tree.xpath("//field[@name='payment_term_id']"):
                    node1.set('readonly', '0')
                for node2 in arch_tree.xpath("//field[@name='billing_period_id']"):
                    node2.set('readonly', '0')
            form_view.sudo().write({'arch': etree.tostring(arch_tree, encoding='unicode')})
        return res
    
    @api.onchange("type_id")
    def onchange_type_id(self):
        if self.type_id.warehouse_id:
            self.warehouse_id = self.type_id.warehouse_id.id

    term_of_delivery_id = fields.Many2one(comodel_name="account.incoterms", string="Term Of Delivery")
    port_of_loading = fields.Char(string="Port Of Loading")
    shipment_by_id = fields.Many2one(comodel_name="delivery.carrier", string="Shipment By")
    can_edit_payment_terms = fields.Boolean(
        compute='_compute_can_edit_payment_terms',
        store=False,
    )

    @api.depends('user_id')
    def _compute_can_edit_payment_terms(self):
        for order in self:
            order.can_edit_payment_terms = self.env.user.has_group('hdc_creditlimit_saleteam.group_can_change_payment_terms')
    
    @api.onchange('can_edit_payment_terms')
    def _onchange_payment_term_domain(self):
        if not self.can_edit_payment_terms:
            return {
                'domain': {
                    'payment_term_id': [('is_cash', '=', True)]
                }
            }
        else:
            return {
                'domain': {
                    'payment_term_id': []
                }
            }
    
    sale_team_ids = fields.One2many('crm.team', compute = '_compute_sale_team_ids')
    @api.depends('partner_id')
    def _compute_sale_team_ids(self):
        for rec in self:
            team_ids = self.env['crm.team']

            # 1. จาก Credit Limit
            credit_limit = self.env['customer.credit.limit'].search([
                ('partner_id', '=', rec.partner_id.id)
            ], limit=1)

            if credit_limit and credit_limit.credit_id:
                matching_teams = credit_limit.credit_id.credit_line.mapped('sale_team_id')

                if matching_teams:
                    team_ids |= matching_teams

            # 2. จาก Master Customer
            if rec.partner_id.team_id:
                team_ids |= rec.partner_id.team_id

            # 3. จาก User 
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id),('company_id', '=',rec.company_id.id)], limit=1)
            if employee:
                user_teams = self.env['crm.team'].search([
                    ('sale_employee_ids', 'in', employee.id)
                ])
                team_ids |= user_teams

            # if rec.company_id:
            #     team_ids = team_ids.filtered(lambda t: t.company_id == rec.company_id or not t.company_id)

            # if not rec.team_id and team_ids:
            #     rec.team_id = team_ids[0]
            # rec.team_id = team_ids[0].id if team_ids else False
            rec.sale_team_ids = team_ids
    
    @api.onchange('partner_id')
    def _onchange_partner_id_team_id(self):
        for rec in self:
            team_ids = self.env['crm.team']
            user_employee = self.env['hr.employee']

            # 1. จาก Credit Limit
            credit_limit = self.env['customer.credit.limit'].search([
                ('partner_id', '=', rec.partner_id.id)
            ], limit=1)

            if credit_limit and credit_limit.credit_id:
                matching_teams = credit_limit.credit_id.credit_line.mapped('sale_team_id')
                sale_user_employee = credit_limit.credit_id.credit_line.mapped('sale_user_employee_id')

                if matching_teams:
                    team_ids |= matching_teams
                if sale_user_employee:
                    user_employee |= sale_user_employee

            # 2. จาก Master Customer
            if rec.partner_id.team_id:
                team_ids |= rec.partner_id.team_id

            # 3. จาก User 
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id),('company_id', '=',self.company_id.id)], limit=1)
            if employee:
                user_teams = self.env['crm.team'].search([
                    ('sale_employee_ids', 'in', employee.id)
                ])
                team_ids |= user_teams

            # if rec.company_id:
            #     team_ids = team_ids.filtered(lambda t: t.company_id == rec.company_id or not t.company_id)

            # if not rec.team_id and team_ids:
            #     rec.team_id = team_ids[0]
            rec.team_id = team_ids[0].id if team_ids else False
            rec.user_employee_id = user_employee[0].id if user_employee else False
            if rec.partner_id:
                if rec.env.user.employee_id in rec.team_id.sale_employee_ids:
                    rec.user_employee_id = rec.env.user.employee_id
                else:
                    rec.user_employee_id = False
            
            if credit_limit:
                customer = credit_limit.credit_id.credit_line.filtered(lambda l: l.sale_team_id == rec.team_id)
                if customer:
                    rec.payment_term_id = customer.payment_term_id.id
                    rec.payment_method_id = customer.payment_method_id.id
                    rec.billing_period_id = customer.billing_period_id.id
                    rec.user_employee_id = customer.sale_user_employee_id.id
            rec.sale_manager_employee_id = rec.team_id.user_employee_id
            rec.department_id = rec.team_id.department_id
            # rec.sale_team_ids = team_ids

    @api.onchange('payment_term_id')
    def _onchange_payment_term_id(self):
        if not self.payment_term_id:
            return
        today = fields.Date.today()
        if self.payment_term_id.is_cash:
            self.validity_date = today + timedelta(days=30)
        else:
            days = self.payment_term_id.days
            self.validity_date = today + timedelta(days=days)

    def update_quotation_line_pick_location_id(self):
        for rec in self:
            for line in rec.quotation_line:
                putaway_id = line.env['stock.putaway.rule'].search([('product_id', '=', line.product_id.id), ('company_id', '=', line.company_id.id), ('location_out_id.warehouse_id', '=', line.warehouse_id.id)], limit = 1)
                if putaway_id:
                    line.pick_location_id = putaway_id.location_out_id.id
                else:
                    if self.warehouse_id:
                        line.pick_location_id = line.warehouse_id.out_type_id.default_location_src_id.id

class QuotationLine(models.Model):
    _name = 'quotation.order.line'
    _description = 'Quotation Order Line'
    _order = 'quotation_id, sequence, id'
    _check_company_auto = True

    bom_revision = fields.Char(
        string="Revision",
        compute="_compute_bom_revision",
        store=True
    )

    #แก้ไขบัคให้ชั่วคราว(หน้างาน)เพราะ error หน้างานไม่รู้ว่าแก้ไขถูกจุดหรือไม่
    # @api.depends('product_id', 'quotation_id.company_id')
    def _compute_bom_revision(self):
        for line in self:
            revision = ""
            if line.product_id:
                bom = self.env['mrp.bom']._bom_find(
                    product=line.product_id,
                    company_id=line.quotation_id.company_id.id
                )
                if bom:
                    revision = bom.bom_revision or ""
            line.bom_revision = revision

    quotation_id = fields.Many2one('quotation.order', string='Quotation Reference', required=True, ondelete='cascade', index=True, copy=False)
    validity_date = fields.Date(related='quotation_id.validity_date', string='Validity Date', store=True)
    user_id = fields.Many2one('res.users', related='quotation_id.user_id', string='Salesperson', store=True)
    date_order = fields.Datetime(related='quotation_id.date_order', string='Order Date', store=True)
    quotation_name = fields.Char(related='quotation_id.name', string='Quotation Name', store=True)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Net Amount', readonly=True, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes', context={'active_test': False})
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    product_id = fields.Many2one(
        'product.product', string='Product', domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_default_code = fields.Char(related='product_id.default_code', store=True)
    product_name = fields.Char(related='product_id.name', store=True)
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_no_variant_attribute_value_ids = fields.Many2many('product.template.attribute.value', string="Extra Values", ondelete='restrict')
    salesman_id = fields.Many2one(related='quotation_id.user_id', store=True, string='Salesperson', readonly=True)
    currency_id = fields.Many2one(related='quotation_id.currency_id', depends=['quotation_id.currency_id'], store=True, string='Currency', readonly=True)
    company_id = fields.Many2one(related='quotation_id.company_id', string='Company', store=True, readonly=True, index=True)
    order_partner_id = fields.Many2one(related='quotation_id.partner_id', store=True, string='Customer', readonly=False)
    state = fields.Selection(
        related='quotation_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    triple_discount = fields.Char('Discount')
    discount_pricelist = fields.Float('Unit Price Pricelist', readonly=True)
    rounding_price = fields.Char('Rounding')
    dis_price = fields.Float('Discount price', compute = '_compute_amount')
    is_global_discount = fields.Boolean('is global discount', default = False)
    categ_id = fields.Many2one('product.category', related = 'product_id.categ_id', string = 'Product Category')
    barcode = fields.Char(string = 'Barcode', related = 'product_id.barcode', index = True)
    pick_location_id = fields.Many2one('stock.location', string = 'Location')
    sequence2 = fields.Integer(
        help="Shows the sequence of this line in the sale order.",
        # related="sequence",
        string="No",
        readonly=True,
    )
    barcode = fields.Char(string='Barcode',related='product_id.barcode',index=True)
    qty_available = fields.Float(string='Quantity On Hand', related="product_id.qty_available" , readonly=True,digits="Product Unit of Measure",)
    free_qty = fields.Float(string='Available QTY',digits="Product Unit of Measure" ,compute='_compute_free_qty')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', related='quotation_id.warehouse_id', store=True, readonly=True)
    note = fields.Text('Note')
    sub_discount = fields.Float(string="Sub Disc %", compute='_compute_sub_discount_line')   
    sale_price_marketing = fields.Float(string='Sale Price MKT.', digits='Product Price')
    blanket_order_line = fields.Many2one(
        "sale.blanket.order.line", string="Blanket Order line", copy=False
    )

    modify_type_txt = fields.Char(string="แปลง/Type/Block", related="quotation_id.modify_type_txt") 
    plan_home = fields.Char(string="แบบบ้าน", related="quotation_id.modify_type_txt")
    room = fields.Char(string="ชั้น/ห้อง", related="quotation_id.room")
    
    external_product_id = fields.Many2one('multi.external.product',string="External Product")
    external_customer = fields.Many2one('res.partner', string="External Customer",store=True)
    external_item = fields.Char(string="External Item",store=True)
    barcode_customer = fields.Char(string="Barcode Customer",store=True)
    barcode_modern_trade = fields.Char(string="Barcode Product",store=True)
    description_customer = fields.Text(string="External Description",store=True)

    tags_product_sale_ids = fields.Many2many(related='product_id.tags_product_sale_ids', string='Tags')

    @api.onchange('product_id','product_template_id','quotation_id.partner_id','product_uom')
    def _onchange_external_product(self):
        if self.product_template_id and self.quotation_id.partner_id:
            external_product = self.env['multi.external.product'].search([
                ('product_tmpl_id', '=', self.product_template_id.id),
                ('partner_id', '=', self.quotation_id.partner_id.id),
                # ('uom_id', '=', self.product_id.uom_id.id)
            ], limit=1)

            if not external_product:
                external_product = self.env['multi.external.product'].search([
                    ('product_tmpl_id', '=', self.product_template_id.id),
                    ('company_chain_id', '=', self.quotation_id.partner_id.company_chain_id.id),
                    # ('uom_id', '=', self.product_id.uom_id.id)
                ], limit=1)

            self.external_product_id = external_product.id if external_product else False
            if self.external_product_id:
                barcode_modern_trade_ids = self.external_product_id.barcode_spe_ids.filtered(lambda x: x.uom_id == self.product_uom)
                if barcode_modern_trade_ids:
                    barcode_modern_trade = barcode_modern_trade_ids[0].barcode_modern_trade
                else:
                    barcode_modern_trade = False
                self.external_item = self.external_product_id.name
                self.barcode_customer = self.external_product_id.barcode_modern_trade
                self.barcode_modern_trade = barcode_modern_trade
                self.description_customer = self.external_product_id.product_description
            else:
                self.external_item = False
                self.barcode_customer = False
                self.barcode_modern_trade = False
                self.description_customer = False

    @api.onchange('product_id', 'product_uom_qty')
    def triple_discount_pricelist(self):
        check_product = self.env["product.pricelist.item"].search([("pricelist_id", "=", self.quotation_id.pricelist_id.id),
            ("product_tmpl_id", "=", self.product_id.product_tmpl_id.id),
            ("min_quantity", "<=", self.product_uom_qty)], order='min_quantity desc', limit=1)
        if check_product:
            if check_product.triple_discount:
                self.triple_discount = check_product.triple_discount
                self.discount_pricelist = check_product.dis_price
            else:
                self.triple_discount = ""
                self.discount_pricelist = 0.0

    @api.constrains('price_total')
    def _check_price_total(self):
        for line in self:
            # if line.price_total < 0 and line.is_global_discount is False and line.is_reward_line is False:
            if line.price_total < 0 and line.is_global_discount is False: #แก้ให้ข้ามถ้าติดลบเพราะ promotion
                raise UserError('Net Amount cannot be negative. Please check the order lines.')
            
    @api.depends('triple_discount', 'product_uom_qty', 'price_unit', 'tax_id', 'dis_price', 'rounding_price')
    def _compute_amount(self):
        for line in self:
            total_dis = 0.0
            price_total = line.product_uom_qty * line.price_unit
            if line.triple_discount:
                try:
                    discounts = line.triple_discount.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')
                    for discount in discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for discount in discounts:
                        if discount.endswith("%"):
                            dis_percen = discount.replace("%", "")
                            total_percen = ((price_total)*float(dis_percen))/100
                            price_total -= total_percen
                            total_dis += total_percen
                        else:
                            total_baht = float(discount)
                            price_total -= total_baht
                            total_dis += total_baht
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))

            price = (line.price_unit *line.product_uom_qty) - total_dis

            if line.rounding_price:
                try:
                    rounding_value = float(line.rounding_price[1:])
                    decimal_precision = self.env['decimal.precision'].precision_get('Sale Rounding')
                    rounding_pattern = re.compile(r'^[+-]?\d+(\.\d{1,%d})?$'%decimal_precision)

                    if not rounding_pattern.match(line.rounding_price):
                        raise ValidationError(
                            _('Invalid Rounding format : +20 or -20 with up to %d decimal places'%decimal_precision))

                    if line.rounding_price.startswith("+"):
                        price += rounding_value
                    elif line.rounding_price.startswith("-"):
                        price -= rounding_value
                    else:
                        raise ValidationError(_('Invalid Rounding format : +20 or -20'))
                except:
                    raise ValidationError(_('Invalid Rounding format : +20 or -20'))

            taxes = line.tax_id.compute_all(price, line.quotation_id.currency_id, 1, product = line.product_id,
                                            partner = line.quotation_id.partner_shipping_id)

            price_total = taxes['total_included']

            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': price_total,
                'price_subtotal': taxes['total_excluded'], 'dis_price': total_dis,
                })

            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    def _compute_tax_id(self):
        for line in self:
            line = line.with_company(line.company_id)
            fpos = line.quotation_id.fiscal_position_id or line.quotation_id.fiscal_position_id.get_fiscal_position(line.order_partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda t: t.company_id == line.env.company)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.quotation_id.partner_shipping_id)

    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        # awa: don't know if it's still the case since we need the "product_no_variant_attribute_value_ids" field now
        # to be able to compute the full price

        # it is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.
        no_variant_attributes_price_extra = [
            ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav:
                    ptav.price_extra and
                    ptav not in product.product_template_attribute_value_ids
            )
        ]
        if no_variant_attributes_price_extra:
            product = product.with_context(
                no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
            )

        if self.quotation_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.quotation_id.pricelist_id.id, uom=self.product_uom.id).price
        product_context = dict(self.env.context, partner_id=self.quotation_id.partner_id.id, date=self.quotation_id.date_order, uom=self.product_uom.id)

        final_price, rule_id = self.quotation_id.pricelist_id.with_context(product_context).get_product_price_rule(product or self.product_id, self.product_uom_qty or 1.0, self.quotation_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.quotation_id.pricelist_id.id)
        if currency != self.quotation_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.quotation_id.pricelist_id.currency_id,
                self.quotation_id.company_id or self.env.company, self.quotation_id.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids

        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        lang = get_lang(self.env, self.quotation_id.partner_id.lang).code
        product = self.product_id.with_context(lang = lang, partner = self.quotation_id.partner_id,
            quantity = vals.get('product_uom_qty') or self.product_uom_qty, date = self.quotation_id.date_order,
            pricelist = self.quotation_id.pricelist_id.id, uom = self.product_uom.id)

        vals.update(name = self.with_context(lang = lang).get_sale_order_line_multiline_description_sale(product))

        self._compute_tax_id()

        if self.quotation_id.pricelist_id and self.quotation_id.partner_id:
            vals['price_unit'] = product._get_tax_included_unit_price(self.company_id, self.quotation_id.currency_id,
                self.quotation_id.date_order, 'sale', fiscal_position = self.quotation_id.fiscal_position_id,
                product_price_unit = self._get_display_price(product), product_currency = self.quotation_id.currency_id)
        self.update(vals)

        title = False
        message = False
        result = {}
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s", product.name)
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False

        return result

    def get_sale_order_line_multiline_description_sale(self, product):
        """ Compute a default multiline description for this sales order line.

        In most cases the product description is enough but sometimes we need to append information that only
        exists on the sale order line itself.
        e.g:
        - custom attributes and attributes that don't create variants, both introduced by the "product configurator"
        - in event_sale we need to know specifically the sales order line as well as the product to generate the name:
          the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
        """
        return product.get_product_multiline_description_sale()

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        if not (self.product_id and self.product_uom and
                self.quotation_id.partner_id and self.quotation_id.pricelist_id and
                self.quotation_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('product.group_discount_per_so_line')):
            return

        self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.quotation_id.partner_id.lang,
            partner=self.quotation_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.quotation_id.date_order,
            pricelist=self.quotation_id.pricelist_id.id,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.quotation_id.partner_id.id, date=self.quotation_id.date_order, uom=self.product_uom.id)

        price, rule_id = self.quotation_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.quotation_id.partner_id)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.quotation_id.pricelist_id.id)

        if new_list_price != 0:
            if self.quotation_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.quotation_id.pricelist_id.currency_id,
                    self.quotation_id.company_id or self.env.company, self.quotation_id.date_order or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if (discount > 0 and new_list_price > 0) or (discount < 0 and new_list_price < 0):
                self.discount = discount

    @api.onchange('product_id')
    def _onchange_location_product_id(self):
        putaway_id = self.env['stock.putaway.rule'].search([('product_id', '=', self.product_id.id), ('company_id', '=', self.company_id.id), ('location_out_id.warehouse_id', '=', self.warehouse_id.id)], limit = 1)
        if putaway_id:
            self.pick_location_id = putaway_id.location_out_id.id
        else:
            if self.warehouse_id:
                self.pick_location_id = self.warehouse_id.out_type_id.default_location_src_id.id

    @api.depends('product_id', 'warehouse_id')
    def _compute_free_qty(self):
        StockQuant = self.env['stock.quant']
        for line in self:
            if line.product_id and line.warehouse_id:
                quants = StockQuant.search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', 'child_of', line.warehouse_id.view_location_id.id)
                ])
                line.free_qty = sum(quants.mapped('available_quantity'))
            else:
                line.free_qty = 0.0
    
    @api.depends('triple_discount','price_subtotal','price_total','price_unit','product_id','quotation_id.global_discount','quotation_id.global_discount_total')
    def _compute_sub_discount_line(self):
        for line in self:
            if line.price_unit <= 0:
                line.sub_discount = 0.0
            else:
                std_price = line.product_id.lst_price
                if line.product_id.uom_id:
                    new_qty = line.product_uom._compute_quantity(
                        line.product_uom_qty, line.product_id.uom_id
                    )
                else:
                    new_qty = line.product_uom_qty
                cost = std_price * new_qty
                if cost == 0:
                    line.sub_discount = 0.0
                else:
                    sub_dis = ((cost) - line.price_total) * 100 / (cost)
                    if sub_dis <= 0:
                        line.sub_discount = 0.0
                    else:
                        line.sub_discount = sub_dis
    
    @api.model
    def create(self, values):
        line = super(QuotationLine, self).create(values)
        # We do not reset the sequence if we are copying a complete sale order
        if self.env.context.get("keep_line_sequence"):
            line.quotation_id._reset_sequence()
        return line
    
    def _get_assigned_bo_line(self, bo_lines):
        # We get the blanket order line with enough quantity and closest
        # scheduled date
        assigned_bo_line = False
        date_planned = date.today()
        date_delta = timedelta(days=365)
        for line in bo_lines.filtered(lambda l: l.date_schedule):
            date_schedule = line.date_schedule
            if date_schedule and abs(date_schedule - date_planned) < date_delta:
                assigned_bo_line = line
                date_delta = abs(date_schedule - date_planned)
        if assigned_bo_line:
            return assigned_bo_line
        non_date_bo_lines = bo_lines.filtered(lambda l: not l.date_schedule)
        if non_date_bo_lines:
            return non_date_bo_lines[0]

    def _get_eligible_bo_lines_domain(self, base_qty):
        filters = [
            ("product_id", "=", self.product_id.id),
            ("remaining_qty", ">=", base_qty),
            ("currency_id", "=", self.quotation_id.currency_id.id),
            ("order_id.state", "=", "open"),
        ]
        if self.quotation_id.partner_id:
            filters.append(("partner_id", "=", self.quotation_id.partner_id.id))
        return filters

    def _get_eligible_bo_lines(self):
        base_qty = self.product_uom._compute_quantity(
            self.product_uom_qty, self.product_id.uom_id
        )
        filters = self._get_eligible_bo_lines_domain(base_qty)
        return self.env["sale.blanket.order.line"].search(filters)

    def get_assigned_bo_line(self):
        self.ensure_one()
        eligible_bo_lines = self._get_eligible_bo_lines()
        if eligible_bo_lines:
            if (
                self.blanket_order_line
                and self.blanket_order_line not in eligible_bo_lines
            ):
                self.blanket_order_line = self._get_assigned_bo_line(eligible_bo_lines)
        else:
            self.blanket_order_line = False
        return {"domain": {"blanket_order_line": [("id", "in", eligible_bo_lines.ids)]}}

    @api.onchange("product_id", "order_partner_id")
    def onchange_product_id(self):
        # If product has changed remove the relation with blanket order line
        if self.product_id:
            return self.get_assigned_bo_line()
        return

    @api.onchange("product_uom_qty", "product_uom")
    def product_uom_change(self):
        if self.product_id and not self.env.context.get("skip_blanket_find", False):
            return self.get_assigned_bo_line()

    @api.onchange("blanket_order_line")
    def onchange_blanket_order_line(self):
        bol = self.blanket_order_line
        if bol:
            self.product_id = bol.product_id
            if bol.product_uom != self.product_uom:
                price_unit = bol.product_uom._compute_price(
                    bol.price_unit, self.product_uom
                )
            else:
                price_unit = bol.price_unit
            self.price_unit = price_unit
            if bol.taxes_id:
                self.tax_id = bol.taxes_id
        else:
            if not self.tax_id:
                self._compute_tax_id()
            self.with_context(skip_blanket_find=True).product_uom_change()

    @api.constrains("currency_id")
    def check_currency(self):
        for line in self:
            if line.blanket_order_line:
                if line.currency_id != line.blanket_order_line.order_id.currency_id:
                    raise ValidationError(
                        _(
                            "The currency of the blanket order must match with "
                            "that of the sale order."
                        )
                    )
                
    # @api.model
    # def default_get(self, fields):
    #     rec = super(QuotationLine, self).default_get(fields)
    #     if self.quotation_id:
    #         self.update({
    #             'finance_dimension_1_id': self.finance_dimension_1_id or self.quotation_id.finance_dimension_1_id.id,
    #             'finance_dimension_2_id': self.finance_dimension_2_id or self.quotation_id.finance_dimension_2_id.id,
    #             'finance_dimension_3_id': self.finance_dimension_3_id or self.quotation_id.finance_dimension_3_id.id
    #         })

    #     return rec
    def write(self, vals):
        user_error = False
        if self.blanket_order_line:
            if vals.get("product_uom_qty"):
                now_remain = self.blanket_order_line.remaining_uom_qty
                now_remain += self.product_uom_qty
                now_remain -= vals.get("product_uom_qty")
                if now_remain < 0 :
                    user_error = True
                else:
                    if vals.get("blanket_order_line") is False:
                        vals.pop("blanket_order_line")
        res = super().write(vals)
        if self.blanket_order_line:
            for rec in self :
                now_remain = rec.blanket_order_line.remaining_uom_qty
                if now_remain < 0 :
                        user_error = True
                if user_error:
                    raise UserError(
                                _("ไม่สามารถแก้ไขจำนวน Demand มากกว่าที่กำหนดในสัญญาได้")
                            )

        return res