# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class SettleCommissionsMall(models.Model):
    _inherit = "settle.commissions.mall"
    
    def export_commission_lines(self):
        self.ensure_one()
        report = self.env['ir.actions.report'].search(
        [('report_name', '=', 'export_commission_lines_report_xlsx'),
        ('report_type', '=', 'xlsx')], limit=1)
        report.report_file = 'Commission Sold Out Lines-' + self.name
        return report.report_action(self)
    
    def wizard_import(self):
        self.ensure_one()
        return {
                "name": "Import",
                "type": "ir.actions.act_window",
                "res_model": "wizard.import.commission.mall",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_settle_commissions_mall_id": self.id,},
            }
    
    def print(self):
        self.ensure_one()
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.commission.mall.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_settle_commissions_mall_id": self.id,
                            "default_target_type": self.target_type,},
            }