# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class SettleCommissions(models.Model):
    _inherit = "settle.commissions"
    
    def print(self):
        self.ensure_one()
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.commission.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_settle_commissions_id": self.id,
                            "default_target_type": self.target_type,
                            "default_settle_type": self.settle_type,},
            }
    