# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from datetime import datetime
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError, except_orm
import logging
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class WizardStockMovementReport(models.TransientModel):
    _name = 'wizard.stock.movement.report'
    _description = 'Wizard Stock Movement'

    product_id = fields.Many2many('product.product', string='สินค้า')
    date_from = fields.Date('เริ่มต้น')
    date_to = fields.Date('ถึง')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')

    def get_report(self):
        report = self.env['ir.actions.report'].search(
            [('report_name', '=', 'stock_movement_report_xlsx'),
             ('report_type', '=', 'xlsx')], limit=1)
        return report.report_action(self)
    
    def _prepare_stock_movement_report(self):
        self.ensure_one()
        return {
            "date_from": self.date_from,
            "date_to": self.date_to or fields.Date.context_today(self),
            "product_id": [(6, 0, self.product_id.ids)],
            "warehouse_ids": self.warehouse_ids.ids,
            "company_id":self.company_id.id,
        }
    
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref("hdc_stock_card_report.action_report_stock_movement_report_html")
        vals = action.sudo().read()[0]
        context = vals.get("context", {})
        if context:
            context = safe_eval(context)
        model = self.env["report.stock.movement.report"]
        report = model.create(self._prepare_stock_movement_report())
        context["active_id"] = report.id
        context["active_ids"] = report.ids
        vals["context"] = context
        return vals
