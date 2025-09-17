# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools.misc import clean_context

class MRPMR(models.Model):
    _inherit = 'mrp.mr'

    @api.onchange('company_id')
    def _onchange_company_id(self):
        for line in self.product_line_ids:
            line._onchange_product_id()

class MRProductListLine(models.Model):
    _inherit = 'mr.product.list.line'
    
    free_qty = fields.Float(string='Onhand',digits=(16, 2),compute='_compute_free_qty')
    
    def check_stock_location_not_get(self,data):
        mrp_mr_onhand_location_id = self.env['mrp.mr.onhand.location'].search([('company_id','=',self.mr_id.company_id.id)])
        if mrp_mr_onhand_location_id:
            location_ids = mrp_mr_onhand_location_id.mr_onhand_location_ids.ids
            if location_ids:
                if data.location_id.id not in location_ids:
                    return False
                else:
                    return True
        else:
            return False
    
    def get_stock_onhand_company(self,company_id):
        location_list = self.env['stock.quant'].search([('product_id','=', self.product_id.id),('location_id.usage','=','internal'),('company_id','=', company_id.id)])
        total_available_quantity = 0
        for rec in location_list:
            if self.check_stock_location_not_get(rec) == True:
                total_available_quantity = total_available_quantity + rec.available_quantity
        return total_available_quantity

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id
        if self.product_id:
            company_id = self.mr_id.company_id
            free_qty = self.get_stock_onhand_company(company_id)
            self.free_qty = free_qty
    
    def _compute_free_qty(self):
        for rec in self:
            if rec.product_id:
                company_id = rec.mr_id.company_id
                free_qty = rec.get_stock_onhand_company(company_id)
                rec.free_qty = free_qty

class MRProductListModifyLine(models.Model):
    _inherit = 'mr.product.list.modify.line'
    
    free_qty = fields.Float(string='Onhand',digits=(16, 2),compute='_compute_free_qty')
    
    def check_stock_location_not_get(self,data):
        mrp_mr_onhand_location_id = self.env['mrp.mr.onhand.location'].search([('company_id','=',self.mr_id.company_id.id)])
        if mrp_mr_onhand_location_id:
            location_ids = mrp_mr_onhand_location_id.mr_onhand_location_ids.ids
            if location_ids:
                if data.location_id.id not in location_ids:
                    return False
                else:
                    return True
        else:
            return False
    
    def get_stock_onhand_company(self,company_id):
        location_list = self.env['stock.quant'].search([('product_id','=', self.product_id.id),('location_id.usage','=','internal'),('company_id','=', company_id.id)])
        total_available_quantity = 0
        for rec in location_list:
            if self.check_stock_location_not_get(rec) == True:
                total_available_quantity = total_available_quantity + rec.available_quantity
        return total_available_quantity

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.product_uom = self.product_id.uom_id.id
        if self.product_id:
            company_id = self.mr_id.company_id
            free_qty = self.get_stock_onhand_company(company_id)
            self.free_qty = free_qty
            
    def _compute_free_qty(self):
        for rec in self:
            if rec.product_id:
                company_id = rec.mr_id.company_id
                free_qty = rec.get_stock_onhand_company(company_id)
                rec.free_qty = free_qty
