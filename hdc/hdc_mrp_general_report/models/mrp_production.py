from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import time, datetime, timedelta



class KsMrpProduction(models.Model):
    _inherit = 'mrp.production'

    def print_borrow(self):
        
        return {
                "name": "Borrow Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.borrow.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_picking_id": self.id},
            }
        