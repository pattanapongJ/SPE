from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import time, datetime, timedelta



class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    est_quantity = fields.Float(compute='_compute_est_quantity', string='EST Quantity',default=0.0, digits='Product Unit of Measure',tracking=True,)
    material_requisition_type_id = fields.Many2one('material.requisition.type', string ='Material Requisition Type')
    note = fields.Text("Note")
    partner_id = fields.Many2one('res.partner', string="Customer",tracking=True)

    def search_sale_order(self,origin=None):
        if origin:
            sale_order = self.env["sale.order"].search([('name','=',origin)])
            if len(sale_order) == 0:
                mrp_id_origin = self.env["mrp.production"].search([('name','=',origin)])
                if mrp_id_origin.mr_id:
                    return mrp_id_origin.mr_id
                if mrp_id_origin:
                    sale_order =  self.search_sale_order(mrp_id_origin.origin)
            return sale_order
        
    def set_partner_id(self):
        if self.mr_id.partner_id:
            self.partner_id = self.mr_id.partner_id
        if self.origin:
            sale_order = self.search_sale_order(self.origin)
            if sale_order:
                self.partner_id = sale_order.partner_id
        
    def get_partner_id(self):
        partner_id = False
        if self.mr_id.partner_id:
            partner_id = self.mr_id.partner_id
        if self.origin:
            sale_order = self.search_sale_order(self.origin)
            if sale_order:
                partner_id = sale_order.partner_id
        if self.partner_id:
            partner_id = self.partner_id
        return partner_id   

    def get_partner_id_name(self):
        partner_id = self.get_partner_id()
        if partner_id:
            return partner_id.name  
        return '-'      

    count_mrp_production_state = fields.Integer(string='mrp production state report count', compute='_compute_mrp_production_state_report')

    def _compute_mrp_production_state_report(self):
        for rec in self:
            mrp_production_state_id = rec.env['mrp.production.state'].search([('mrp_id', '=', rec.id),])
            rec.count_mrp_production_state = len(mrp_production_state_id)
            rec.set_partner_id()
    
    def action_view_mrp_production_state_report(self):
        mrp_production_state_id = self.env['mrp.production.state'].search([('mrp_id', '=', self.id),])
        partner_id = self.get_partner_id()
        action = {
            'name': 'Mrp Production State Report', 
            'type': 'ir.actions.act_window', 
            'res_model': 'mrp.production.state', 
            'view_mode': "tree,form", 
            "domain": [("id", "in", mrp_production_state_id.ids)],
            "context": {"default_mrp_id": self.id,}}
        return action
    
    def print(self):
        self.ensure_one()
        material_requisition_type_id = self.env['material.requisition.type'].search([('is_default','=',True)],limit=1)
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.mrp.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.state,
                            "default_mrp_id": self.id,
                            "default_material_requisition_type_id": material_requisition_type_id.id,},
            }
    
    @api.depends('move_raw_ids.quantity_done')
    def _compute_est_quantity(self):
        for rec in self:
            est_quantity = 0
            for move in rec.move_raw_ids:
                bom_line_id = rec.env['mrp.bom.line'].search([('bom_id', '=', rec.bom_id.id),('product_id', '=', move.product_id.id)])
                if bom_line_id.product_est_qty > 0 :
                    consumed = move.quantity_done
                    if consumed == 0:
                        consumed = move.product_uom_qty
                    est_quantity = consumed/bom_line_id.product_est_qty
            rec.est_quantity = est_quantity

    def get_iso_name(self,picking_type_id,doc_name):
        for rec in self:
            if picking_type_id:
                iso_number = rec.env["iso.operation.type"].search([('operation_type_id','=',picking_type_id),
                                                                    ('doc_name','=',doc_name)],limit=1)
            return iso_number.iso_number if iso_number else '-'