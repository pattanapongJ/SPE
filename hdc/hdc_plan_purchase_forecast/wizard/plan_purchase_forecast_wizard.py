# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PlanPurchaseForecast(models.TransientModel):
    _name = "plan.purchase.forecast"
    _description = "Plan Purchase Forecast"
    
    date_before = fields.Selection(
        selection=[("four", "4 เดือน"),
                   ("six", "6 เดือน"),
                   ("one_year", "1 ปี")],
        string="ข้อมูลย้อนหลัง",default="four")

    def action_print(self):
        report = self.env['ir.actions.report'].search(
            [('report_name', '=', 'plan_purchase_forecast_xlsx'), ('report_type', '=', 'xlsx')], limit = 1)
        return report.report_action(self)
