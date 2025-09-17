# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class SearchForecastPurchase(models.Model):
    _name = 'search.forecast.purchase'
    _description = "Search Forecast Purchase For Create RFQ"

    name = fields.Char("Name")
    product_ids = fields.Many2many('product.product', string="Product")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=False, domain="[('supplier', '=', True)]",)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses', readonly=False)
    product_categ_ids = fields.Many2many('product.category', string='Product Category', readonly=False)
    suggest_status = fields.Selection([
        ('status_1', 'Suggest 1'),
        ('status_2', 'Suggest 2'),
        ('status_3', 'Suggest 3'),
        ('status_4', 'Suggest 4'),
        ('status_5', 'Suggest 5'),
    ], string="Suggest Status")

    product_type = fields.Selection([
        ('plan_to_order', 'Buy'),
        ('plan_to_stock', 'Make To Stock'),
    ], string="Product Type",default='plan_to_order')

    @api.depends('product_line_ids')
    def _compute_selected_count(self):
        for order in self:
            selected_count = 0
            if self.product_line_ids:
                selected_count = sum(bool(line.selected) for line in self.product_line_ids)
            order.update({
                'selected_count': selected_count,
            })
    selected_count = fields.Float('Selected count', compute="_compute_selected_count")
    product_line_ids = fields.One2many("search.forecast.purchase.line", "search_id", string="Product Lines")
    def search_action(self):
        self.product_line_ids.unlink()

        supplierinfo = []
        product_tmpl_ids = []
        if self.partner_id:
            supplierinfo = self.env['product.supplierinfo'].search([('name', '=', self.partner_id.id)])
            
            for line in supplierinfo:
                if line.product_tmpl_id:
                    product_tmpl_ids.append(line.product_tmpl_id.id)

        search_obj = []
        if self.product_ids.ids:
            search_obj += [('id', 'in', self.product_ids.ids)]
        if self.product_categ_ids.ids:
            search_obj += [('categ_id', 'in', self.product_categ_ids.ids)]
        if len(product_tmpl_ids) > 0:
            search_obj += [('product_tmpl_id', 'in', product_tmpl_ids)]
        
        search_product_ids = self.env['product.product'].search(search_obj)

        line = []
        for product in search_product_ids:
            line_add = False
            plan_forecast = product.get_plan_purchase()
            plan_to_order = plan_forecast.get("plan_to_order")
            plan_to_stock = plan_forecast.get("plan_to_stock")
            if self.product_type == "plan_to_order":
                if plan_to_order == "Yes":
                    line_add = True
            if self.product_type == "plan_to_stock":
                if plan_to_stock == "Yes":
                    line_add = True
            if line_add:
                line.append((0, 0, {
                    'product_id': product.id,
                    'product_categ_id': product.categ_id.id,
                    'moq_stock': product.moq_stock,
                    'spq_stock': product.spq_stock,
                    'suggest_qty': plan_forecast.get("po_order"),
                }))

        self.product_line_ids = line

    def create_purchase_order_action(self):

        if self.product_line_ids:
            selected_count = sum(bool(line.selected) for line in self.product_line_ids)
            if selected_count == 0:
                raise ValidationError(_('ไม่สามารถ Generate RFQ ได้. โปรดเลือกรายการที่ต้องการ Generate RFQ'))
            
            return {
                'name': "Create Request For Quotation",
                'view_mode': 'form',
                'res_model': 'request.for.quotation.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_search_id': self.id,
                    'default_company_id': self.company_id.id,
                    'default_partner_id': self.partner_id.id,
                }
            }

    def selected_all_action(self):
        for line in self.product_line_ids:
            line.selected = True
    
    def clear_all_action(self):
        # self.status_sale_ids = self.default_state()
        self.product_ids = False
        self.product_categ_ids = False
        self.warehouse_ids = False
        self.product_line_ids.unlink()

    def create_mrp_request_action(self):
        if self.product_line_ids:
            selected_count = sum(bool(line.selected) for line in self.product_line_ids)
            if selected_count == 0:
                raise ValidationError(_('ไม่สามารถ Generate Mrp Request ได้. โปรดเลือกรายการที่ต้องการ Generate Mrp Request'))
            
            return {
                'name': "Create Request For MRP Request",
                'view_mode': 'form',
                'res_model': 'request.for.mrp.request.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_search_id': self.id,
                    'default_company_id': self.company_id.id,
                }
            }

class SearchForecastPurchaseLine(models.Model):
    _name = 'search.forecast.purchase.line'

    selected = fields.Boolean('Choose', default=False)
    search_id = fields.Many2one("search.forecast.purchase")
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    name = fields.Char(related='product_id.name', string="Name")
    product_categ_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouses', readonly=True)
    moq_stock = fields.Float(related='product_id.moq_stock', string="MOQ")
    spq_stock = fields.Float(related='product_id.spq_stock', string="SPQ")
    suggest_qty = fields.Integer(string="Suggest QTY", readonly=True)
    rfq_qty = fields.Integer(string="RFQ QTY")
    suggest_status = fields.Selection([
        ('status_1', 'Suggest 1'),
        ('status_2', 'Suggest 2'),
        ('status_3', 'Suggest 3'),
        ('status_4', 'Suggest 4'),
        ('status_5', 'Suggest 5'),
    ], string="Suggest Status")