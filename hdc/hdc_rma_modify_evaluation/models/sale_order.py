# Copyright 2022 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api,fields, models
from odoo.tools.safe_eval import safe_eval

class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_repair_type_id = fields.Boolean(related='type_id.is_repair',string='Is Repair Sales Types')
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type", string="Repair Factory" ,domain="[('addition_operation_types.code', '=', 'AO-06'),('is_factory', '=', True)]"
    )
    to_warehouse = fields.Many2one("stock.warehouse", string = "Delivery Transfer")

    # def action_sale_ok2(self):
    #     if self.type_id.is_repair:
    #         line_ids = []
    #         if self.order_line:
    #             for item in self.order_line:
    #                 if item.display_type == False:
    #                     if item.is_global_discount == False:
    #                         line_ids.append([0, 0, {
    #                             "name": item.name,
    #                             "product_id": item.product_id.id,
    #                             "product_uom": item.product_uom.id,
    #                             "product_uom_qty": item.product_uom_qty,
    #                             "location_id": self.picking_type_id.default_location_src_id.id,
    #                             "description_picking":item.name,}])

    #         picking_inter = self.env["stock.picking"].create({
    #             "order_id":self.id,
    #             "partner_id":self.partner_id.id,
    #             "team_id":self.team_id.id,
    #             "picking_type_id": self.picking_type_id.id,
    #             "location_id": self.picking_type_id.default_location_src_id.id,
    #             "location_dest_id": self.picking_type_id.default_location_dest_id.id,
    #             "to_warehouse":self.to_warehouse.id,
    #             "transit_location":self.to_warehouse.lot_stock_id.id,
    #             "move_lines": line_ids,
    #             })

    #         super(SaleOrder, self).action_sale_ok2()
    #     else:
    #         return super(SaleOrder, self).action_sale_ok2()
        
    def action_inter(self):
        picking_ids = self.env['stock.picking'].search([('order_id', '=', self.id)])
        action = {
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
        }
        if len(picking_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': picking_ids[0].id,
            })
        else:
            action.update({
                'domain': [('id', 'in', picking_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action