from odoo import SUPERUSER_ID, _, api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    # def process(self):
    #     res = super().process()
    #     stock_picking = self.env['stock.picking'].browse(self.pick_ids.id)
    #     if stock_picking.operation_types == "Request spare parts Type":
    #         stock_picking.write({'state': 'ready_delivery'})
    #         stock_picking.write({'transfer_date': fields.Datetime.now()})
    #     return res

    # def process_cancel_backorder(self):
    #     res = super().process_cancel_backorder()
    #     stock_picking = self.env['stock.picking'].browse(self.pick_ids.id)
    #     if stock_picking.operation_types == "Request spare parts Type":
    #         stock_picking.write({'state': 'ready_delivery'})
    #         stock_picking.write({'transfer_date': fields.Datetime.now()})
    #     return res