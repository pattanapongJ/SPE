# Copyright 2014-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    customer_in_charge = fields.Many2one(
        'res.users',
        string='Customer In Charge',
    )

    driver_agents = fields.Many2one(string = "Driver", comodel_name = "res.partner", domain="[('agent', '=', True),('agent_type', '=', 'driver')]")

    picking_type_code = fields.Selection(string="Picking Type Code", related='picking_type_id.code', store=True, readonly=True)