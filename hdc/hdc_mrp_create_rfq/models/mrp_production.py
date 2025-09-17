# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta, datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class MrpBomInherit(models.Model):
    _inherit = 'mrp.bom'

    partner_id_vendor = fields.Many2one('res.partner', string='Vendor')

class MrpProductionInherit(models.Model):
    _inherit = 'mrp.production'

    partner_id_vendor = fields.Many2one('res.partner', string='Vendor' ,related="bom_id.partner_id_vendor")

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        if self.bom_id:
            self.partner_id_vendor = self.bom_id.partner_id_vendor.id

    def action_open_wizard_mrp_create_rfq_no_line(self, create_rfq):
        # picking_type_id = self.env["stock.picking.type"].search([("warehouse_id","=",self.picking_type_id.warehouse_id.id)], limit = 1)
        
        context = {
            'default_mo_id': self.id,
            'default_location_id': self.location_src_id.id,
            'default_location_dest_id': self.location_dest_id.id,
            'default_picking_type_id': self.picking_type_id.id,
            'default_partner_id': create_rfq[0]['partner_id_vendor'] if create_rfq else False,
            'default_purchase_type': create_rfq[0]['purchase_type'] if create_rfq else False,
            'default_currency_id': create_rfq[0]['currency_id'] if create_rfq else False,
            'default_order_deadline': create_rfq[0]['order_deadline'] if create_rfq else False,
        }
        return {
                'type': 'ir.actions.act_window',
                'name': 'Create RFQ',
                'res_model': 'wizard.mrp.create.rfq',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }

    def action_open_wizard_mrp_create_rfq(self):
        # picking_type_id = self.env["stock.picking.type"].search([("warehouse_id","=",self.picking_type_id.warehouse_id.id)], limit = 1)
        mo_line = []
        gross_unit_price = 0.0

        for mo in self.move_raw_ids:
            vendor_pricelist = self.env["product.supplierinfo"].search([("name","=",self.partner_id_vendor.id),
                                                                    ("product_tmpl_id","in",[mo.product_id.product_tmpl_id.id,False]),
                                                                    ("product_id","=",[mo.product_id.id,False]),
                                                                    ("min_qty","<=",mo.product_uom_qty),
                                                                    "|",
                                                                    ("date_start", "=", False),
                                                                    ("date_start", "<=", datetime.now().date()),
                                                                    "|",
                                                                    ("date_end", "=", False),
                                                                    ("date_end", ">=", datetime.now().date()),
                                                                    ], order="create_date desc",limit=1)
            if vendor_pricelist:
                gross_unit_price = vendor_pricelist.price
            else:
                gross_unit_price = 0


            mo_line.append((0, 0, {
                'product_id': mo.product_id.id,
                'product_uom_qty': mo.product_uom_qty,
                'gross_unit_price': gross_unit_price,
            }))

        
        context = {
            'default_mo_id': self.id,
            'default_location_id': self.location_src_id.id,
            'default_location_dest_id': self.location_dest_id.id,
            'default_picking_type_id': self.picking_type_id.id,
            'default_partner_id': self.partner_id_vendor.id or False,
            'default_order_line_ids': mo_line,
        }
        return {
                'type': 'ir.actions.act_window',
                'name': 'Create RFQ',
                'res_model': 'wizard.mrp.create.rfq',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }

    create_rfq_count = fields.Integer(
        "Count of generated PO",
        compute='_compute_create_rfq_count')

    @api.depends('state','procurement_group_id.stock_move_ids.created_purchase_line_id.order_id', 'procurement_group_id.stock_move_ids.move_orig_ids.purchase_line_id.order_id')
    def _compute_create_rfq_count(self):
        for production in self:
            origin = production.name
            production.create_rfq_count = self.env['purchase.order'].search_count([('origin', '=', origin),("is_create_rfq", "=", True)])


    def action_view_create_rfq(self):
        self.ensure_one()
        purchase_order_ids = self.env['purchase.order'].search([('origin', '=', self.name),("is_create_rfq", "=", True)]).ids
        action = {
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
        }
        if len(purchase_order_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': purchase_order_ids[0],
            })
        else:
            action.update({
                'name': _("Purchase Order generated from %s", self.name),
                'domain': [('id', 'in', purchase_order_ids)],
                'view_mode': 'tree,form',
            })
        return action
        