# Copyright 2022 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api,fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_dewalt = fields.Boolean(compute='_compute_is_dewalt', string='Dewalt')
    
    @api.depends('repair_order_ids')
    def _compute_is_dewalt(self):
        for rec in self:
            check = False
            if rec.repair_order_ids:
                if rec.repair_order_ids.claim_id:
                    if rec.repair_order_ids.claim_id.is_dewalt:
                        check = True
            rec.is_dewalt = check

    def action_sale_ok2(self):
        if self.type_id.is_repair and self.is_dewalt is False:
            line_ids = []
            if self.order_line:
                for item in self.order_line:
                    if item.display_type == False:
                        if item.is_global_discount == False:
                            line_ids.append([0, 0, {
                                "name": item.name,
                                "product_id": item.product_id.id,
                                "product_uom": item.product_uom.id,
                                "product_uom_qty": item.product_uom_qty,
                                "location_id": self.to_warehouse.lot_stock_id.id,
                                "description_picking":item.name,
                                "location_dest_id" : self.picking_type_id.default_location_src_id.id,}])

            picking_inter = self.env["stock.picking"].create({
                "order_id":self.id,
                "partner_id":self.partner_id.id,
                "team_id":self.team_id.id,
                "picking_type_id": self.picking_type_id.id,
                "location_id": self.picking_type_id.default_location_src_id.id,
                "location_dest_id": self.picking_type_id.default_location_dest_id.id,
                "to_warehouse":self.to_warehouse.id,
                "transit_location":self.to_warehouse.lot_stock_id.id,
                "move_lines": line_ids,
                })

            return super(SaleOrder, self).action_sale_ok2()
        else:
            return super(SaleOrder, self).action_sale_ok2()
        

    def action_cancel(self):
        check_cancel = False
        for rec in self.repair_order_ids:
            for line in rec.operations:
                line.sale_line_id = False
        return super(SaleOrder, self).action_cancel()
    
    def print_dewalt_report(self):
        self.ensure_one()
        return {
                "name": "Dewalt Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.sale.dewalt.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {
                            # "default_state": self.state,
                            "default_sale_id": self.id,
                            },

            }
    def action_confirm(self):        
        if self.type_id.is_dewalt :
            location_id = self.env["stock.location"].search([("is_dewalt", "=", True), ("company_id", "=", self.company_id.id),("warehouse_id","=",self.warehouse_id.id)], limit=1)
            if len(location_id) == 0:
                raise Warning(
                _("ไม่พบ Location Dewalt ของ Warehouse %s",self.warehouse_id.name)
                )
            res = super(SaleOrder, self).action_confirm()
            if self.picking_ids:
                for pick in self.picking_ids:
                    if pick.state in ['waiting','confirmed','draft','assigned']:
                        for line in pick.move_ids_without_package:
                            line.location_id = location_id
                            line.state = 'draft'
                        pick.state = 'draft'
                        pick.location_id = location_id
                        pick.action_confirm()
                        pick.action_assign()
    
                        for line in pick.move_ids_without_package:
                            line.qty_counted = line.product_uom_qty
                        pick.action_confirm_warehouse()
                            
            return res
        else:
            return super(SaleOrder, self).action_confirm()
     