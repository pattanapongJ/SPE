# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from datetime import datetime
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError, except_orm
import logging

_logger = logging.getLogger(__name__)


class WizardStockReceiveReport(models.TransientModel):
    _name = 'wizard.stock.movement.report'
    _description = 'Wizard Stock Movement'

    product_id = fields.Many2many('product.product', string='สินค้า')
    date_from = fields.Date('เริ่มต้น')
    date_to = fields.Date('ถึง')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    def get_report(self):
        report = self.env['ir.actions.report'].search(
            [('report_name', '=', 'stock_movement_report_xlsx'),
             ('report_type', '=', 'xlsx')], limit=1)
        return report.report_action(self)
