# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PlanPurchaseForecast(models.TransientModel):
    _name = "report.scrap"
    _description = "Report Scrap"

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    state = fields.Selection(
        [("draft", "Draft"),
         ("done", "Done"),
         ("cancel", "Cancel")], string="Status")

    def action_print(self):
        report = self.env['ir.actions.report'].search(
            [('report_name', '=', 'report_scrap_xlsx'), ('report_type', '=', 'xlsx')], limit = 1)
        return report.report_action(self)
