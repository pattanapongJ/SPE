from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super(StockPicking, self).button_validate()

        for picking in self:
            if picking.picking_type_id.code == "incoming": 
                for move in picking.move_lines:
                    sale_line = move.sale_line_id
                    if sale_line:
                        sale_line.return_delivery_qty += move.quantity_done

        return res
