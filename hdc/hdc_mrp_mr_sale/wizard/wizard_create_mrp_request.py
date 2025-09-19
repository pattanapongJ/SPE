# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.exceptions import UserError, ValidationError

class WizardSaleCreateMRLine(models.TransientModel):
    _name = 'wizard.sale.create.mr.line'
    _description = 'Sale Create MR Line'

    mr_id = fields.Many2one('wizard.sale.create.mr', string='MR Reference', ondelete='cascade')
    product_id = fields.Many2one("product.product", string="Product",domain="[('id', 'in', available_product_ids)]",required=True)
    moq_stock = fields.Float(related="product_id.moq_stock", string="MOQ")
    demand_qty = fields.Float("Demand", default=0.0, required=True, index=True)
    package = fields.Char("Package")
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", required=True, index=True)
    available_product_ids = fields.Many2many('product.product', compute='_compute_available_product_ids', store=False, string='Available Products')

    @api.depends('mr_id.sale_order_id')
    def _compute_available_product_ids(self):
        for line in self:
            if line.mr_id.sale_order_id:
                products = line.mr_id.sale_order_id.order_line.mapped('product_id').filtered(lambda p: p.route_ids.filtered(lambda r: r.name == "Manufacture"))
                line.available_product_ids = products
            else:
                line.available_product_ids = self.env['product.product']

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id

class WizardSaleCreateMRModifyLine(models.TransientModel):
    _name = 'wizard.sale.create.mr.modify.line'
    _description = 'Sale Create MR Modify Line'

    mr_id = fields.Many2one('wizard.sale.create.mr', string='MR Reference', ondelete='cascade')
    product_id = fields.Many2one("product.product", string="Product", required=True ,domain=[('type', '=', 'product'), ('bom_ids', '!=', False)])
    name = fields.Text(string='Description', required=True)
    demand_qty_modify = fields.Float("Demand Modify",default=1.0, required=True)
    product_uom = fields.Many2one('uom.uom', 'UoM',required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            default_code = self.product_id.default_code or ''
            self.name = '[' + default_code + '] ' + self.product_id.name
        else:
            self.name = ''
        self.product_uom = self.product_id.uom_id.id

class WizardSaleCreateMR(models.TransientModel):
    _name = 'wizard.sale.create.mr'
    _description = 'Wizard Sale Create MR'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    product_line_ids = fields.One2many('wizard.sale.create.mr.line', 'mr_id')
    product_line_modify_ids = fields.One2many('wizard.sale.create.mr.modify.line', 'mr_id')
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    department_id  = fields.Many2one('hr.department', string='Production', required=True, tracking=True, index=True)
    request_type = fields.Many2one('request.type.mr', string='Request Type', required=True, tracking=True, index=True)
    product_type = fields.Many2one('product.type.mr', string='Product Type', required=True, tracking=True, index=True)
    request_date = fields.Datetime(string='Request Date', default=fields.Datetime.now, tracking=True)
    delivery_date = fields.Date(string='Delivery Date', default=fields.Datetime.now, tracking=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        tracking=True
    )
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Factory',
        domain="[('code', '=', 'mrp_operation'), ('company_id', '=', company_id)]",
        required=True
    )
    @api.model
    def _get_domain_picking_do_type(self):
        addition = self.env["addition.operation.type"].search([("code", "=", "AO-06")], limit=1)
        picking_do_type_ids = self.env['stock.picking.type'].search([
            ("addition_operation_types", "=", addition.id),
        ])
        return [('id','in',picking_do_type_ids.ids)]
    
    picking_type_do_id = fields.Many2one(
        'stock.picking.type', 'Delivery',
        domain=lambda self: self._get_domain_picking_do_type(), check_company=True,)
    remark = fields.Text(string="Remark")
    user_request = fields.Many2one('res.users', string='Request', default=lambda self: self.env.user, tracking=True, index=True)
    is_modify = fields.Boolean(related='request_type.is_modify',string='Is Modify')
    
    @api.onchange('product_type')
    def _onchange_product_type(self):
        if self.product_type.picking_type_id:
            self.picking_type_id = self.product_type.picking_type_id
        if self.product_type.department_id:
            self.department_id = self.product_type.department_id
        if self.product_type.out_factory_picking_type_id :
            self.picking_type_do_id = self.product_type.out_factory_picking_type_id

    def generate_new_mr(self):
        move_raw_ids = []
        if self.request_type.is_modify == False:
            for product_line in self.product_line_ids:
                if product_line.demand_qty <= 0:
                    raise UserError(_("Please Check Demand of Product '%s'.") % product_line.product_id.name)
                move_raw_ids.append((0, 0, {
                    'product_id': product_line.product_id.id,
                    'uom_id': product_line.uom_id.id,
                    'demand_qty': product_line.demand_qty,
                    'package': product_line.package,
                }))
        
            mr_id = self.env['mrp.mr'].create({
                'request_type': self.request_type.id,
                'partner_id': self.partner_id.id,
                'product_type': self.product_type.id,
                'picking_type_id': self.picking_type_id.id,
                'department_id': self.department_id.id,
                'sale_order_id': self.sale_order_id.id,
                'request_date': self.request_date,
                'delivery_date': self.delivery_date,
                'product_line_ids': move_raw_ids,
                'remark': self.remark,
            })
        elif self.request_type.is_modify == True:
            for product_line in self.product_line_modify_ids:
                if product_line.demand_qty_modify <= 0:
                    raise UserError(_("Please Check Demand of Product '%s'.") % product_line.product_id.name)
                move_raw_ids.append((0, 0, {
                    'product_id': product_line.product_id.id,
                    'name': product_line.name,
                    'product_uom': product_line.product_uom.id,
                    'demand_qty_modify': product_line.demand_qty_modify,
                }))
        
            mr_id = self.env['mrp.mr'].create({
                'request_type': self.request_type.id,
                'partner_id': self.partner_id.id,
                'product_type': self.product_type.id,
                'picking_type_id': self.picking_type_id.id,
                'picking_type_do_id': self.picking_type_do_id.id,
                'department_id': self.department_id.id,
                'sale_order_id': self.sale_order_id.id,
                'request_date': self.request_date,
                'delivery_date': self.delivery_date,
                'product_line_modify_ids': move_raw_ids,
                'remark': self.remark,
            })
        return {
            "name": _(mr_id.name),
            "view_mode": "form",
            "res_id": mr_id.id,
            "res_model": "mrp.mr",
            "view_id": self.env.ref('hdc_mrp_mr.mrp_mr_view_form').id,
            "type": "ir.actions.act_window",
        }
    
    @api.onchange('sale_order_id')
    def order_id_change(self):
        product_line_ids_data = []
        for rec in self.sale_order_id.order_line:
            if rec.product_id.route_ids.filtered(lambda l: l.name == "Manufacture"):
                data_rec = (0, 0, {
                    "product_id": rec.product_id.id,
                    "demand_qty": rec.product_uom_qty,
                    "uom_id": rec.product_uom.id,
                })
                product_line_ids_data.append(data_rec)
        self.update({
            'product_line_ids': product_line_ids_data,
        })
