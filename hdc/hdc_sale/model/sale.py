# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
import re

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "HDC Sale"
    _order = 'priority desc, id desc'

    @api.onchange('partner_id')
    def _get_domain_partner_id_sale_order(self):
        partner_invoice_id = ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id),
                              ('id', 'in', self.partner_id.child_ids.ids), ('type', '=', 'invoice')]
        partner_shipping_id = ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id),
                              ('id', 'in', self.partner_id.child_ids.ids), ('type', '=', 'delivery')]
        res = {}
        domain_partner = ['|', ('customer', '=', True), '&', ('customer', '=', False), ('supplier', '=', False), ('parent_id', '=', False)]
        res['domain'] = {'partner_invoice_id': partner_invoice_id, 'partner_shipping_id': partner_shipping_id, 'partner_id': domain_partner}
        return res

    def _get_domain_user_id(self):
        if self.team_id:
            return [('groups_id', '=', {}), ('share', '=', False),
                    ('company_ids', '=', self.company_id), ('id', 'in', self.team_id.member_ids.ids)]
        return []

    customer_po = fields.Char(string="")
    priority = fields.Selection( [('0', 'Low'), ('1', 'Normal') , ('2', 'High') , ('3', 'Urgent')], 'Priority', default='0', index=True)
    
    delivery_time = fields.Many2one(
        'delivery.time', string='Delivery Time',tracking=True
    )
    
    delivery_terms = fields.Many2one(
        'account.incoterms', string='Delivery Terms',tracking=True
    )
    
    offer_validation = fields.Many2one(
        'offer.validation', string='Offer Validation',tracking=True
    )

    sale_spec = fields.Many2one('res.users', string = 'Sale Spec')
    user_sale_agreement = fields.Many2one('res.users', string = 'Administrator', default=lambda self: self.env.user)

    # member_ids = fields.One2many('res.users', 'team_id', related = "team_id.member_ids", store = True)
    member_ids = fields.Many2many('res.users',compute="_compute_member_ids")
    user_id = fields.Many2one('res.users', string = 'Salesperson', index = True, tracking = 2,
        default = lambda self: self.env.user,
                              domain=lambda self: "[('id', 'in', member_ids),('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
            self.env.ref("sales_team.group_sale_salesman").id
        ),)
    # sale_manager_id = fields.Many2one("res.users", string="Sale Manager")
    sale_manager_id = fields.Many2one("res.users", string="Sale Manager")
    modify_type_txt = fields.Char(string="แปลง/Type/Block")
    plan_home = fields.Char(string="แบบบ้าน")
    room = fields.Char(string = "ชั้นห้อง")
    requested_ship_date = fields.Date(string="Requested ship date")
    requested_receipt_date = fields.Date(string = "Requested receipt date",default=fields.Date.context_today)
    delivery_trl = fields.Many2one("delivery.round", string="สายส่ง TRL")
    delivery_trl_description = fields.Char(related="delivery_trl.name", string="สายส่ง TRL Description")
    po_date = fields.Date(string = "PO Date")
    expire_date = fields.Date(string="Expire Date PO")
    customer_contact_date = fields.Char(string="Customer Contact No.")
    delivery_company = fields.Many2one("company.delivery.round", string="Mode of delivery")
    delivery_company_description = fields.Char(related="delivery_company.name", string="Mode of delivery Description")
    remark = fields.Char(string="Remark")
    outline_agreement = fields.Char(string="Outline Agreement")
    
    port_of_loading = fields.Char(string="Port Of Loading")
    shipment_by_id = fields.Many2one(comodel_name="delivery.carrier", string="Shipment By")

    def default_get(self, fields_list):
        defaults = super(SaleOrder, self).default_get(fields_list)
        team_id = defaults.get('team_id')
        team = self.env['crm.team'].search([('id', '=', team_id)])
        defaults['sale_manager_id'] = team.user_id.id
        return defaults

    @api.onchange('delivery_trl')
    def change_delivery_trl(self):
      if self.delivery_trl:
        return {'domain': {'delivery_company':[('status_active', '=', True),('delivery_line', '=', self.delivery_trl.id)]}}
      else:
          return {'domain': {'delivery_company':[('status_active', '=', True)]}}
    
    @api.depends('team_id')
    def _compute_member_ids(self):
        for rec in self:
            rec.member_ids = rec.team_id.member_ids.ids

    @api.onchange("team_id")
    def _onchange_member_ids(self):
        member_ids = []
        if self.team_id:
            member_ids = self.team_id.member_ids.ids
            return {"domain": {"user_id": [('id', 'in', member_ids)]}}
        return {"domain": {"user_id": []}}

    @api.depends('global_discount','global_discount_update','order_line','order_line.product_id')
    def _compute_global_discount_total(self):
        for order in self:
            amount_untaxed = 0.0
            for line in order.order_line:
                if line.product_id != order.default_product_global_discount:
                    amount_untaxed += line.price_subtotal

            global_discount_total = 0.0
            if order.order_line:
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

    global_discount = fields.Char(string="Global Discount")
    global_discount_update = fields.Char()
    global_discount_total = fields.Float(string="Global Discount Total", compute='_compute_global_discount_total', store=True)

    @api.onchange('global_discount_update','global_discount_total','global_discount')
    def _onchange_global_discount_update(self):
        for order in self:
            if order.global_discount:
                order.global_discount_update = order.global_discount_total
    
    @api.onchange('offer_validation')
    def _onchange_offer_validation(self):
        if self.offer_validation:
            if self.offer_validation.weeks:
                weeks = self.offer_validation.weeks
                if weeks:
                    today = datetime.today()
                    new_validity_date = today + timedelta(weeks=weeks)
                    self.validity_date = new_validity_date.date()
            elif self.offer_validation.months: 
                months = self.offer_validation.months
                if months:
                    today = datetime.today().replace(day=1) 
                    new_validity_date = today + relativedelta(months=months)
                    self.validity_date = new_validity_date.date()
    
    @api.onchange('delivery_time')
    def _onchange_delivery_time(self):
        if self.delivery_time:
            if self.delivery_time.weeks:
                weeks = self.delivery_time.weeks
                if weeks:
                    today = datetime.today()
                    new_validity_date = today + timedelta(weeks=weeks)
                    self.commitment_date = new_validity_date.date()
            elif self.delivery_time.months: 
                months = self.delivery_time.months
                if months:
                    today = datetime.today().replace(day=1) 
                    new_validity_date = today + relativedelta(months=months)
                    self.commitment_date = new_validity_date.date()
    
    @api.model
    def _default_global_discount(self):
        global_discount = self.env['ir.config_parameter'].sudo().get_param('hdc_discount.global_discount_default_product_id')
        return global_discount if global_discount else False
    
    default_product_global_discount = fields.Many2one('product.product', default=_default_global_discount)
    
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.sale_spec:
            res["sale_spec"] = self.sale_spec.id
        if self.sale_manager_id:
            res["sale_manager_id"] = self.sale_manager_id.id
        if self.user_sale_agreement:
            res["user_sale_agreement"] = self.user_sale_agreement.id
        return res
    
    @api.model
    def _get_default_team_new(self):
        return False

    team_id = fields.Many2one(
        'crm.team', 'Sales Team',
        # change_default=True, default=_get_default_team_new, check_company=True,  # Unrequired company
        # domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('id','in',sale_team_ids)]"
        )

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
            rec.team_id = team_ids[0].id if team_ids else False
            rec.user_employee_id = user_employee[0].id if user_employee else False
            if rec.env.user.employee_id in rec.team_id.sale_employee_ids:
                rec.user_employee_id = rec.env.user.employee_id
            # else:
            #     rec.user_employee_id = False

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
            
    
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _description = "HDC Sale"
    
    barcode = fields.Char(string='Barcode',related='product_id.barcode',index=True)
    triple_discount = fields.Char('Discount')
    qty_available = fields.Float(string='Quantity On Hand', related="product_id.qty_available" , readonly=True,digits="Product Unit of Measure",)
    free_qty = fields.Float(string='Available QTY',digits="Product Unit of Measure" ,compute='_compute_free_qty')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', related='order_id.warehouse_id', store=True, readonly=True)
    
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