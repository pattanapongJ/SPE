from odoo import api, fields, models

class SaleOrderTypology(models.Model):
   _inherit = "sale.order.type"

   is_borrow = fields.Boolean(string='Is Borrow')
   picking_borrow_type_id = fields.Many2one(
      comodel_name="stock.picking.type", 
      string="Picking Borrow Type", 
      domain=lambda self: self._get_picking_type_domain()
   )
   picking_type_deduct_borrow_id = fields.Many2one(
      comodel_name="stock.picking.type", 
      string="Picking Type Deduct", 
      domain=[("code", "=", "outgoing")],
      help="Deduct products from borrow stock.",

   )

   @api.model
   def _get_picking_type_domain(self):
      """
      Define a dynamic domain for the picking_type_id field
      based on the addition operation type, company, and warehouse.
      """
      addition = self.env["addition.operation.type"].search([("code", "=", "AO-02")], limit=1)
      return [('addition_operation_types', '=', addition.id)]

   # @api.onchange('company_id', 'warehouse_id')
   # def _onchange_picking_type(self):
   #    """
   #    Update domain of picking_type_id based on company and warehouse.
   #    """
   #    addition = self.env["addition.operation.type"].search([("code", "=", "AO-02")], limit=1)
   #    if addition and self.company_id and self.warehouse_id:
   #       # Set the domain dynamically using onchange method
   #       return {
   #             'domain': {
   #                'picking_type_id': [
   #                   ('addition_operation_types', '=', addition.id),
   #                   ('company_id', '=', self.company_id.id),
   #                   ('warehouse_id', '=', self.warehouse_id.id)
   #                ]
   #             }
   #       }
   #    else:
         
   #       return {'domain': {'picking_type_id': []}}
