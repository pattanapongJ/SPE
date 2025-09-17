# Copyright 2019 Kitti Upariphutthiphong <kittiu@ecosoft.co.th>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

class Repair(models.Model):
    _inherit = "repair.order"

    requisition_id = fields.Many2one('stock.picking', string='Source Document', copy=False)