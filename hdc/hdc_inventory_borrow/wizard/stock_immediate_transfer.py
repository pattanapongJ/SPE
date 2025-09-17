
from odoo import _, api, fields, models
from odoo.exceptions import UserError

class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'
    
    # def process(self):
    #     res = super().process()
    #     stock_picking = self.env['stock.picking'].browse(self.pick_ids.id)
    #     if stock_picking.operation_types == "Request spare parts Type":
    #         stock_picking.write({'state': 'ready_delivery'})
    #         stock_picking.write({'transfer_date': fields.Datetime.now()})
    #     return res
