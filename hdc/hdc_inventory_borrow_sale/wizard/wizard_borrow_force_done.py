# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo import fields, models
from odoo.exceptions import UserError, ValidationError

class CheckForceDone(models.TransientModel):
    _name = "check.force.done"
    _description = "Check Force Done"

    sale_order_id = fields.Many2one(
        comodel_name="sale.order", string="Reason", required=True
    )

    def confirm_done(self):
        addition = self.env["addition.operation.type"].search([("code", "=", "AO-02")], limit=1)
        picking_type = self.env["stock.picking.type"].search([("addition_operation_types", "=", addition.id)])
        picking = self.env["stock.picking"].search([("sale_borrow", "=", self.sale_order_id.id),("picking_type_id", "in", picking_type.ids)])
        for picking_id in picking:
            if picking_id.state =='ready_delivery':
                picking_id.force_done()
        self.sale_order_id.action_sale_ok()