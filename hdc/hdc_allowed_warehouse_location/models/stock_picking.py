
from odoo import api, fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    user_ids = fields.Many2many(related='warehouse_id.user_ids')
        

class Picking(models.Model):
    _inherit = "stock.picking"

    def _get_user_warehouse_domain(self):
        return ['|', ('warehouse_id', '=', False), ('warehouse_id', 'in', self.env.user.allowed_warehouse_ids.ids)]
    
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)]}, domain=_get_user_warehouse_domain)
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)],'confirmed': [('readonly', False)],'assigned': [('readonly', False)]}, domain=_get_user_warehouse_domain)
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True, readonly=True,
        states={'draft': [('readonly', False)]}, domain=_get_user_warehouse_domain)