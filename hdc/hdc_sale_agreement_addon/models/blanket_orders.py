# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree
from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from collections import defaultdict
from datetime import datetime, timedelta, date
import re

class BlanketOrder(models.Model):
    # _name = "sale.blanket.order"
    _inherit = "sale.blanket.order"
    # _inherit = ["sale.blanket.order","bs.base.finance.dimension"]

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
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
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

        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            values['team_id'] = self.env['crm.team'].with_context(
                default_team_id=self.partner_id.team_id.id
            )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)], user_id=user_id)
        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id
        if len(self.ref_sale_id) == 0:
            self.update(values)

    def _default_validity_date(self):
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_quotation_validity_days'):
            days = self.env.company.quotation_validity_days
            if days > 0:
                return fields.Date.to_string(datetime.now() + timedelta(days))
        return False

    @api.model
    def _default_warehouse_id(self):
        return self.env.user._get_default_warehouse_id()
    
    def default_get(self, fields_list):
        defaults = super(BlanketOrder, self).default_get(fields_list)
        team_id = defaults.get('team_id')
        team = self.env['crm.team'].search([('id', '=', team_id)])
        defaults['sale_manager_id'] = team.user_id.id
        return defaults

    inter_company_transactions = fields.Boolean(related = "sale_type_id.inter_company_transactions")
    partner_id = fields.Many2one("res.partner",string="Customer",readonly=True,states={"draft": [("readonly", False)]},)
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Account',required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id),('parent_id','=',partner_id), ('type', '=', 'invoice')]")
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address', required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id),('parent_id','=',partner_id), ('type', '=', 'delivery')]")
    customer_po = fields.Char(string = "Customer PO No.",copy=False)
    outline_agreement = fields.Char(string="Outline Agreement")
    po_date = fields.Date(string = "PO Date")
    expire_date = fields.Date(string="Expire Date PO")
    customer_contact_date = fields.Char(string="Customer Contact No.")
    priority = fields.Selection( [('0', 'Low'), ('1', 'Normal') , ('2', 'High') , ('3', 'Urgent')], 'Priority', default='0', index=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',required=True,default=_default_warehouse_id, check_company=True)
    contact_person = fields.Many2one('res.partner', string='Contact Person', readonly=False)
    validity_date = fields.Date(string='Expiration' , default = _default_validity_date)
    modify_type_txt = fields.Char(string="แปลง/Type/Block")
    plan_home = fields.Char(string="แบบบ้าน")
    room = fields.Char(string = "ชั้นห้อง")
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position',domain="[('company_id', '=', company_id)]", check_company=True,)
    sale_manager_id = fields.Many2one("res.users", string="Sale Manager")
    remark = fields.Char(string="Remark")
    requested_ship_date = fields.Date(string="Requested ship date")
    requested_receipt_date = fields.Date(string = "Requested receipt date",default=fields.Date.context_today)
    delivery_trl = fields.Many2one("delivery.round", string="สายส่ง TRL")
    delivery_trl_description = fields.Char(related="delivery_trl.name", string="สายส่ง TRL Description")
    delivery_company = fields.Many2one("company.delivery.round", string="Mode of delivery")
    delivery_company_description = fields.Char(related="delivery_company.name", string="Mode of delivery Description")
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
    days_delivery = fields.Char(string="Days Delivery")

    max_line_sequence = fields.Integer(
        string="Max sequence in lines", compute="_compute_max_line_sequence", store=True
    )
    total_discount_amount_new = fields.Float(string="Total Discount", compute='_compute_total_discount')

    rounding_untax = fields.Char(string='Rounding Untaxed Amount')
    rounding_taxes = fields.Char(string='Rounding Taxes')
    rounding_total = fields.Char(string='Rounding Total')

    days_delivery = fields.Integer(string="Days Delivery")

    billing_route_id = fields.Many2one(comodel_name='account.billing.route', string="Billing Route")
    billing_place_id = fields.Many2one(comodel_name='account.billing.place', string="Billing Place")
    billing_terms_id = fields.Many2one(comodel_name='account.billing.terms', string="Billing Terms")
    payment_period_id = fields.Many2one(comodel_name='account.payment.period', string="Payment Period")

    branch_id = fields.Many2one('res.branch', string='Branch')
    tag_ids = fields.Many2many('crm.tag', string='Tags')
    agreement_done = fields.Boolean(string='agreement done' ,compute='_compute_agreement_done', copy=False,default=False)

    
    @api.constrains('customer_po')
    def _check_customer_po_unique(self):
        for order in self:
            if order.customer_po:
                domain = [
                    ('customer_po', '=', order.customer_po),
                    ('partner_id', '=', order.partner_id.id),
                    ('id', '!=', order.id),  # Exclude the current order
                ]
                duplicate_orders = self.search(domain)
                if duplicate_orders:
                    raise ValidationError("Customer PO No must be unique.")

    def _compute_agreement_done(self):
        precision = self.env["decimal.precision"].precision_get( "Product Unit of Measure")
        for rec in self:
            if float_is_zero(
                sum(rec.line_ids.mapped("remaining_uom_qty")),
                precision_digits=precision,
            ):
                rec.agreement_done = True
            else:
                rec.agreement_done = False
                
    def action_force_done(self):
        self.state = "done"

    @api.onchange('fiscal_position_id')
    def _onchange_fiscal_position_id(self):
        for line in self.line_ids:
            fpos = self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda t: t.company_id == line.env.company)
            line.taxes_id = fpos.map_tax(taxes, line.product_id, self.partner_shipping_id)

    # @api.onchange('finance_dimension_1_id')
    # def onchange_finance_dimension_1_id(self):
    #     self.line_ids.filtered(lambda x: not x.display_type).write({
    #         'finance_dimension_1_id': self.finance_dimension_1_id.id
    #     })

    # @api.onchange('finance_dimension_2_id')
    # def onchange_finance_dimension_2_id(self):
    #     self.line_ids.filtered(lambda x: not x.display_type).write({
    #         'finance_dimension_2_id': self.finance_dimension_2_id.id
    #     })

    # @api.onchange('finance_dimension_3_id')
    # def onchange_finance_dimension_3_id(self):
    #     self.line_ids.filtered(lambda x: not x.display_type).write({
    #         'finance_dimension_3_id': self.finance_dimension_3_id.id
    #     })

    @api.onchange('line_ids', 'line_ids.price_unit', 'line_ids.price_subtotal', 'line_ids.triple_discount',
                  'global_discount', 'global_discount_total', 'write_date', 'line_ids.original_uom_qty')
    def _compute_sub_discount_amount(self):
        for order in self:
            sub_discount = 0.0
            percen_discount = 0.0
            total_std_price = 0.0
            total_subtotal = 0.0
            for line in order.line_ids:
                if line.product_id and line.product_id.lst_price > 0 and line.original_uom_qty > 0:
                    std_price = line.product_id.lst_price
                    if line.product_id.uom_id:
                        new_qty = line.product_uom._compute_quantity(line.original_uom_qty, line.product_id.uom_id)
                    else:
                        new_qty = line.original_uom_qty
                    # หาผลรวมของ public price * product uom qty * factor
                    # total_std_price += std_price * line.original_uom_qty * ratio
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
    
    @api.onchange('line_ids', 'line_ids.price_unit', 'line_ids.price_subtotal', 'line_ids.triple_discount',
                  'global_discount', 'global_discount_total', 'write_date', 'line_ids.original_uom_qty')
    def _compute_total_discount(self):
        for order in self:
            total_discount = 0.0
            total_percen_discount = 0.0
            total_std_price = 0.0
            total_subtotal = 0.0
            
            for line in order.line_ids:
                if line.product_id and line.product_id.lst_price > 0 and line.original_uom_qty > 0:
                    std_price = line.product_id.lst_price
                    line_price_subtotal = line.price_subtotal
                    line_sub_discount = order.sub_discount_amount
                    
                    if line.product_id.uom_id:
                        new_qty = line.product_uom._compute_quantity(
                            line.original_uom_qty, line.product_id.uom_id
                        )
                    else:
                        new_qty = line.original_uom_qty
 
                    #หาผลรวมของ public price * product uom qty * factor
                    total_std_price += std_price * new_qty
                    
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

    @api.onchange('line_ids', 'line_ids.price_total')
    def _compute_amount_before_discount(self):
        for order in self:
            amount_untaxed = sum(line.price_total for line in order.line_ids if not line.is_global_discount)
            order.amount_before_discount = amount_untaxed

    @api.depends('global_discount','global_discount_update','line_ids','line_ids.product_id')
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

    @api.depends("line_ids")
    def _compute_max_line_sequence(self):
        """Allow to know the highest sequence entered in sale order lines.
        Then we add 1 to this value for the next sequence.
        This value is given to the context of the o2m field in the view.
        So when we create new sale order lines, the sequence is automatically
        added as :  max_sequence + 1
        """
        for sale in self:
            sale.max_line_sequence = max(sale.mapped("line_ids.sequence") or [0]) + 1

    def _reset_sequence(self):
        for order in self:
            current_sequence = 1
            max_sequence = 0
            global_discount_line = None

            for line in sorted(order.line_ids, key=lambda x: (x.sequence, x.id)):
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
        return super(BlanketOrder, self.with_context(keep_line_sequence=True)).copy(
            default
        )
    
    def action_rounding_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Total Rounding',
            'view_mode': 'form',
            'res_model': 'wizard.blanket.orders.change.total',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_rounding_untax': self.rounding_untax,
                'default_rounding_taxes': self.rounding_taxes,
                'default_rounding_total': self.rounding_total,
            },
        }
    
    def recalculate_global_discount(self):
        return True
    
    @api.onchange('partner_id')
    def _onchange_partner_id_addon(self):
        if self.partner_id.billing_route_id:
            self.billing_route_id = self.partner_id.billing_route_id.id
        if self.partner_id.billing_place_id:
            self.billing_place_id = self.partner_id.billing_place_id.id
        if self.partner_id.billing_terms_id:
            self.billing_terms_id = self.partner_id.billing_terms_id.id
        if self.partner_id.payment_period_id:
            self.payment_period_id = self.partner_id.payment_period_id.id

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(BlanketOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            form_view = self.env.ref('hdc_sale_agreement_addon.sale_blanket_order_inherit_addon')
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
    
    def create_sale_order(self):
        """
        Open a confirmation wizard with language-specific messages
        """
        lang = self.env.user.lang
        if lang == "th_TH":
            message = _("วันที่ของใบเสนอราคาหมดอายุแล้ว กรุณาติดต่อพนักงานขาย/พนักงานรับจอง หรือคุณต้องการสร้างใบสั่งซื้อต่อ?")
        else:
            message = _("The quotation date has expired. You need to contact the sales representative, or would you like to create a sale order?")
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Expiration QT/SA'),
            'res_model': 'sale.blanket.order.confirmation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message': message,
                'default_blanket_order_id': self.id,
            },
        }
    
    @api.onchange("sale_type_id")
    def onchange_sale_type_id(self):
        for order in self:
            # if order.sale_type_id and order.sale_type_id.pricelist_id:
            #     order.pricelist_id = order.sale_type_id.pricelist_id
            if order.sale_type_id.warehouse_id:
                order.warehouse_id = order.sale_type_id.warehouse_id.id
            if order.sale_type_id.branch_id:
                order.branch_id = order.sale_type_id.branch_id

    term_of_delivery_id = fields.Many2one(comodel_name="account.incoterms", string="Term Of Delivery")

    @api.model
    def create(self, values):
        if values.get("sale_type_id"):
            sa_type = self.env["sale.order.type"].browse(values["sale_type_id"])
            if sa_type.sa_sequence_id:
                values["name"] = sa_type.sa_sequence_id.next_by_id()

        result = super(BlanketOrder, self).create(values)
        result._reset_sequence()
        return result
    
    def write(self, vals):
        if vals.get("sale_type_id"):
            sa_type = self.env["sale.order.type"].browse(vals["sale_type_id"])
            if sa_type.sequence_id:
                for record in self:
                    if (
                        record.state in {"draft"}
                        and record.sale_type_id.sequence_id != sa_type.sequence_id
                    ):
                        new_vals = vals.copy()
                        if sa_type.sa_sequence_id:
                            vals["name"] = sa_type.sa_sequence_id.next_by_id() or _('New')
                        else:
                            vals['name'] = self.env['ir.sequence'].next_by_code('sale.blanket.order') or _('New')
                        super(BlanketOrder, record).write(new_vals)
                    else:
                        super(BlanketOrder, record).write(vals)
                return True
        res = super().write(vals)
        return res

    port_of_loading = fields.Char(string="Port Of Loading")
    shipment_by_id = fields.Many2one(comodel_name="delivery.carrier", string="Shipment By")
    
    pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Pricelist",
        required=True,
        readonly=True,
        domain = "['|', ('company_id', '=', False), ('company_id', '=', company_id),('id','in',pricelist_ids)]",
        states={"draft": [("readonly", False)]},
    )

    team_id = fields.Many2one(
        "crm.team",
        string="Sales Team",
        # check_company = True,
        # domain = "['|', ('company_id', '=', False), ('company_id', '=', company_id), ('id','in',sale_team_ids)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    
    sale_team_ids = fields.One2many('crm.team', compute = '_compute_sale_team_ids')
    pricelist_ids = fields.One2many('product.pricelist', compute = '_compute_pricelist_ids')

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


    @api.depends('partner_id','user_id', 'sale_type_id')
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
            if order.sale_type_id and order.sale_type_id.pricelist_id:
                pricelist_from_sale_type = order.sale_type_id.pricelist_id
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
            if order.sale_type_id and order.sale_type_id.pricelist_id:
                pricelist_from_sale_type = order.sale_type_id.pricelist_id
                exists = self.env['product.pricelist.customer'].search_count([
                    ('partner_id', '=', order.partner_id.id),
                    ('pricelist_id', '=', pricelist_from_sale_type.id)
                ])
                if exists:
                    all_pricelists |= pricelist_from_sale_type

            order.pricelist_id = all_pricelists[0].id if all_pricelists else False



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
            
class BlanketOrderLine(models.Model):
    _name = "sale.blanket.order.line"
    _inherit = "sale.blanket.order.line"
    # _inherit = ["sale.blanket.order.line","bs.base.finance.dimension"]

    state = fields.Selection(
        related='order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    return_qty = fields.Float(string='Return QTY', digits="Product Unit of Measure",compute='_compute_quantities', default=0.00) 
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
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
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', related='order_id.warehouse_id', store=True, readonly=True)
    note = fields.Text('Note')
    sub_discount = fields.Float(string="Sub Disc %", compute='_compute_sub_discount_line')  
    name = fields.Text(string='Description', tracking=True, required=True)
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=False,
        domain=[("sale_ok", "=", True)],
    )
    product_uom = fields.Many2one("uom.uom", string="Unit of Measure", required=False)
    price_unit = fields.Float(string="Unit Price", required=False, digits="Product Price")
    original_uom_qty = fields.Float(
        string="Original quantity",
        required=False,
        default=1,
        digits="Product Unit of Measure",
    )
    discount_pricelist = fields.Float('Unit Price Pricelist', readonly=True)
    is_deposit = fields.Boolean(
        string="Is a down payment", copy=False
    )

    modify_type_txt = fields.Char(string="แปลง/Type/Block", related="order_id.modify_type_txt") 
    plan_home = fields.Char(string="แบบบ้าน", related="order_id.plan_home")
    room = fields.Char(string="ชั้น/ห้อง", related="order_id.room")
    
    external_product_id = fields.Many2one('multi.external.product',string="External Product")
    external_customer = fields.Many2one('res.partner', string="External Customer",store=True)
    external_item = fields.Char(string="External Item",store=True)
    barcode_customer = fields.Char(string="Barcode Customer",store=True)
    barcode_modern_trade = fields.Char(string="Barcode Product",store=True)
    description_customer = fields.Text(string="External Description",store=True)

    tags_product_sale_ids = fields.Many2many(related='product_id.tags_product_sale_ids', string='Tags')


    @api.onchange('product_id','product_id.product_tmpl_id','order_id.partner_id','product_uom')
    def _onchange_external_product(self):
        if self.product_id.product_tmpl_id and self.order_id.partner_id:
            external_product = self.env['multi.external.product'].search([
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('partner_id', '=', self.order_id.partner_id.id),
                # ('uom_id', '=', self.product_id.uom_id.id)
            ], limit=1)

            if not external_product:
                external_product = self.env['multi.external.product'].search([
                    ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                    ('company_chain_id', '=', self.order_id.partner_id.company_chain_id.id),
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

    @api.onchange('product_id')
    def _onchange_location_product_id(self):
        putaway_id = self.env['stock.putaway.rule'].search([('product_id', '=', self.product_id.id), ('company_id', '=', self.company_id.id), ('location_out_id.warehouse_id', '=', self.warehouse_id.id)], limit = 1)
        if putaway_id:
            self.pick_location_id = putaway_id.location_out_id.id
        else:
            if self.warehouse_id:
                self.pick_location_id = self.warehouse_id.out_type_id.default_location_src_id.id

    @api.onchange('product_id', 'original_uom_qty')
    def triple_discount_pricelist(self):
        check_product = self.env["product.pricelist.item"].search([("pricelist_id", "=", self.order_id.pricelist_id.id),
            ("product_tmpl_id", "=", self.product_id.product_tmpl_id.id),
            ("min_quantity", "<=", self.original_uom_qty)], order='min_quantity desc', limit=1)
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
            if line.price_total < 0 and line.is_global_discount is False:
                raise UserError('Net Amount cannot be negative. Please check the order lines.')
            
    @api.onchange("product_id", "original_uom_qty")
    def onchange_product(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        if self.product_id:
            name = self.product_id.name
            if not self.product_uom:
                self.product_uom = self.product_id.uom_id.id
            if self.order_id.partner_id and float_is_zero(
                self.price_unit, precision_digits=precision
            ):
                self.price_unit = self._get_display_price(self.product_id)
            # if self.product_id.code:
            #     name = "[{}] {}".format(name, self.product_id.code)
            if self.product_id.description_sale:
                name = self.product_id.description_sale
            self.name = name

            fpos = self.order_id.fiscal_position_id or self.order_id.fiscal_position_id.get_fiscal_position(self.order_id.partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = self.product_id.taxes_id.filtered(lambda t: t.company_id == self.env.company)
            self.taxes_id = fpos.map_tax(taxes, self.product_id, self.order_id.partner_shipping_id)

    # @api.model
    # def default_get(self, fields):
    #     rec = super(BlanketOrderLine, self).default_get(fields)
    #     if self.order_id:
    #         self.update({
    #             'finance_dimension_1_id': self.finance_dimension_1_id or self.order_id.finance_dimension_1_id.id,
    #             'finance_dimension_2_id': self.finance_dimension_2_id or self.order_id.finance_dimension_2_id.id,
    #             'finance_dimension_3_id': self.finance_dimension_3_id or self.order_id.finance_dimension_3_id.id
    #         })

    #     return rec
    
    @api.depends('triple_discount', 'original_uom_qty', 'price_unit', 'taxes_id', 'dis_price', 'rounding_price')
    def _compute_amount(self):
        for line in self:
            total_dis = 0.0
            price_total = line.price_unit
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

            price = (line.price_unit - total_dis)*line.original_uom_qty

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

            taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, 1, product = line.product_id,
                                            partner = line.order_id.partner_shipping_id)

            price_total = taxes['total_included']

            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': price_total,
                'price_subtotal': taxes['total_excluded'], 'dis_price': total_dis,
                })

            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.taxes_id.invalidate_cache(['invoice_repartition_line_ids'], [line.taxes_id.id])

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

    @api.depends('triple_discount','price_subtotal','price_total','price_unit','product_id','order_id.global_discount','order_id.global_discount_total')
    def _compute_sub_discount_line(self):
        for line in self:
            if line.price_unit <= 0:
                line.sub_discount = 0.0
            else:
                std_price = line.product_id.lst_price
                if line.product_id.uom_id:
                    new_qty = line.product_uom._compute_quantity(
                        line.original_uom_qty, line.product_id.uom_id
                    )
                else:
                    new_qty = line.original_uom_qty
                cost = std_price * new_qty
                if cost == 0:
                    line.sub_discount = 0.0
                else:
                    sub_dis = ((cost) - line.price_total) * 100 / (cost)
                    if sub_dis <= 0:
                        line.sub_discount = 0.0
                    else:
                        line.sub_discount = sub_dis
    
    _sql_constraints = [
        ('accountable_required_fields',
            "CHECK(display_type IS NOT NULL OR (product_id IS NOT NULL AND product_uom IS NOT NULL))",
            "Missing required fields on accountable sale order line."),
        ('non_accountable_null_fields',
            "CHECK(display_type IS NULL OR (product_id IS NULL AND price_unit = 0 AND original_uom_qty = 0 AND product_uom IS NULL))",
            "Forbidden values on non-accountable sale order line"),
    ]

    @api.model
    def create(self, values):
        if values.get('display_type'):
            values.update(product_id=False, original_uom_qty=0,price_unit=0,product_uom=False)
        line = super(BlanketOrderLine, self).create(values)
        # We do not reset the sequence if we are copying a complete sale order
        if self.env.context.get("keep_line_sequence"):
            line.order_id._reset_sequence()
        return line
    
    def write(self, line_values):
        res = super(BlanketOrderLine, self).write(line_values)
        self.order_id._reset_sequence()
        return res
    
    def _compute_quantities(self):
        for line in self:
            sale_lines = line.sale_lines
            line.ordered_uom_qty = sum(
                sl.product_uom._compute_quantity(sl.product_uom_qty, line.product_uom)
                for sl in sale_lines
                if sl.order_id.state != "cancel" and (line.id == sl.blanket_order_line.id)
            )
            line.invoiced_uom_qty = sum(
                sl.product_uom._compute_quantity(sl.qty_invoiced, line.product_uom)
                for sl in sale_lines
                if sl.order_id.state != "cancel" and (line.id == sl.blanket_order_line.id)
            )
            line.delivered_uom_qty = sum(
                sl.product_uom._compute_quantity(sl.qty_delivered, line.product_uom)
                for sl in sale_lines
                if sl.order_id.state != "cancel" and (line.id == sl.blanket_order_line.id)
            )
            return_qty = sum(
                sl.product_uom._compute_quantity(sl.return_delivery_qty, line.product_uom)
                for sl in sale_lines
                if sl.order_id.state != "cancel" and (line.id == sl.blanket_order_line.id)
            )
            line.return_qty = return_qty
            line.remaining_uom_qty = line.original_uom_qty - line.ordered_uom_qty + return_qty
            line.remaining_qty = line.product_uom._compute_quantity(
                line.remaining_uom_qty, line.product_id.uom_id
            )
