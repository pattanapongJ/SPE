# Copyright 2021 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

# Odoo:
from odoo import api, fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    user_ids = fields.Many2many("res.users")
    responsible_id = fields.Many2one("res.users", string="Responsible")
    warehouse_description = fields.Char(string="Description")
    code = fields.Char('Short Name', required=True, size=15, help="Short name used to identify your warehouse")