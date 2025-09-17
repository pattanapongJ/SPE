# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools.misc import clean_context

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    mr_count = fields.Integer(compute='_compute_mr_count', string='mr_count')
    
    def _compute_mr_count(self):
        for order in self:
            order.mr_count = self.env['mrp.mr'].search_count([('sale_order_id', '=', order.id)])
            
    def act_manufacturing_request(self):
        if self.mr_count == 1:
            mr_id = self.env['mrp.mr'].search([('sale_order_id', '=', self.id)],limit=1)
            mrp_request_action = {
                'name':"Manufacturing Request",
                'view_mode':'form',
                'res_model':'mrp.mr',
                'type':'ir.actions.act_window',
                'view_id':self.env.ref('hdc_mrp_mr.mrp_mr_view_form').id,
                'res_id':mr_id.id
            }
        else:
            mrp_request_action = {
                'name':"Manufacturing Request",
                'view_mode':'tree,form',
                'res_model':'mrp.mr',
                'type':'ir.actions.act_window',
                'views':[(self.env.ref('hdc_mrp_mr.mrp_mr_view_tree').id, 'tree'),
                         (self.env.ref('hdc_mrp_mr.mrp_mr_view_form').id, 'form')],
                'domain':[('sale_order_id', '=', self.id)]
            }
        return mrp_request_action
    
    def open_wizard_mrp_request(self):
        picking_type_id = self.env['stock.picking.type'].search([
            ('code', '=', 'mrp_operation'),
            ('warehouse_id.company_id', '=', self.company_id.id),
        ], limit=1).id
        return {
                'type': 'ir.actions.act_window',
                'name': 'Create Manufacturing Request',
                'res_model': 'wizard.sale.create.mr',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_sale_order_id': self.id,
                            'default_partner_id':  self.partner_id.id,
                            'default_picking_type_id':  picking_type_id,
                            'default_company_id':  self.company_id.id,
                            },
            }

class MRPMR(models.Model):
    _inherit = 'mrp.mr'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    is_sent_sale_order = fields.Boolean(string='Is Sent Sale Order')

    def add_sale_order_line(self):
        if self.sale_order_id:
            if len(self.product_line_modify_ids)>0:
                for order_line in self.product_line_modify_ids:
                    if order_line.is_refurbish == False:
                        product = order_line.product_id
                    else:
                        product = order_line.product_refurbish_id
                    sale_order_line_id = self.env["sale.order.line"].search([("order_id", "=", self.sale_order_id.id),("product_id", "=", product.id)])
                    if sale_order_line_id:
                        sale_order_line_id.product_uom_qty = sale_order_line_id.product_uom_qty + order_line.demand_qty_modify
                    else:
                        fpos = self.sale_order_id.fiscal_position_id or self.sale_order_id.fiscal_position_id.get_fiscal_position(self.sale_order_id.partner_id.id)
                        taxes = product.taxes_id.filtered(lambda t: t.company_id == self.env.company)
                        tax_id = fpos.map_tax(taxes, product, self.sale_order_id.partner_shipping_id)
                        sale_order_line = self.env['sale.order.line'].create({
                            'order_id': self.sale_order_id.id,
                            'product_id': product.id,
                            'name': product.name,
                            'pick_location_id': self.picking_type_do_id.default_location_src_id.id,  
                            'product_uom_qty': order_line.demand_qty_modify,
                            'product_uom': product.uom_id.id,
                            'tax_id':tax_id,
                        })

    def _compute_product_line_modify_ids(self):
        for mr in self:
            mr.hide_btn_create_receive = False
            mr.hide_btn_modify_transfer = False
            mr.hide_btn_create_mo_modify = False
            mr.hide_btn_create_transfer_modify = False
            if len(mr.product_line_modify_ids)>0:
                if all(product_line.demand_qty_modify > 0 for product_line in mr.product_line_modify_ids):
                    if all((product_line.demand_qty_modify - product_line.receive_qty_modify - product_line.receive_qty_modify_draft) <= 0 for product_line in mr.product_line_modify_ids):
                        mr.hide_btn_create_receive = True
                    if all(product_line.receive_qty_modify_factory == product_line.demand_qty_modify for product_line in mr.product_line_modify_ids):
                        mr.hide_btn_modify_transfer = True
                    if all(product_line.product_qty_mo == product_line.demand_qty_modify for product_line in mr.product_line_modify_ids):
                        mr.hide_btn_create_mo_modify = True
                    if all(product_line.produced_qty == product_line.demand_qty_modify for product_line in mr.product_line_modify_ids):
                        if mr.delivery_method == 'm2o' and mr.state == "in_progress":
                            mr.auto_create_transfer_modify()
                        mr.write({'state': 'delivery'})   
                    if all(product_line.delivery_qty == product_line.demand_qty_modify and product_line.delivery_qty > 0 for product_line in mr.product_line_modify_ids):
                        mr.hide_btn_create_transfer_modify = True
                        mr.write({'state': 'done'})
                        if mr.is_sent_sale_order == False:
                            mr.add_sale_order_line()
                            mr.is_sent_sale_order = True