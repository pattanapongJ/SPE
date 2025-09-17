# Copyright 2022 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models, api, _


class RepairType(models.Model):
    _inherit = "repair.type"

    sale_type = fields.Many2one(
        comodel_name="sale.order.type", string="Sale Order Type", domain="[('is_repair', '=', True)]"
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    @api.onchange('create_sale_order')
    def _onchange_create_sale_order(self):
        if not self.create_sale_order:
            self.sale_type = False
            
    borrow_picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Borrow Picking Type",
        help="Borrow Picking Type",
    )