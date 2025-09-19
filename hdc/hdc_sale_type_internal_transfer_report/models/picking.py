# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
# from BeautifulSoup import BeautifulSoup as BSHTML

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def do_internal_tranfer_print_picking(self):
        for record in self:
            if record.order_id.type_id.is_booth and record.picking_type_id.code == 'internal':
                self.ensure_one()
                return {
                    "name": "Report",
                    "type": "ir.actions.act_window",
                    "res_model": "wizard.sale.type.report",
                    "view_mode": 'form',
                    'target': 'new',
                    "context": {
                        "default_picking_id": self.id,
                        "default_state": self.state
                        },
                }
            else:
                return super().do_internal_tranfer_print_picking()
            
    def do_return_from_booth_print_picking(self):
        self.ensure_one()
        return {
            "name": "Report",
            "type": "ir.actions.act_window",
            "res_model": "wizard.sale.type.return.booth.report",
            "view_mode": 'form',
            'target': 'new',
            "context": {
                "default_picking_id": self.id,
                "default_state": self.state
                },
        }
