# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
# from BeautifulSoup import BeautifulSoup as BSHTML

class WizardGeneratePickingListReport(models.TransientModel):
    _name = 'generate.picking.list.report'
    _description = "Generate Picking List Report"

    picking_list_ids = fields.Many2many(
        comodel_name='picking.lists',
        string='Picking Lists',
    )

    generate_line_ids = fields.One2many(
        comodel_name='generate.picking.list.report.line',
        inverse_name='generate_report_id',
        string='Picking List Lines'
    )

    date = fields.Datetime("Pick Date", default=fields.Datetime.now)
    checker = fields.Many2one('res.users', string='Checker')
    checker_date = fields.Datetime("Checker Date")
    barcode_date = fields.Date(string="Barcode Date")

    project_name = fields.Many2one('sale.project', string='Project Name')
    # partner_id = fields.Many2one("res.partner", string="Customer", domain="[('customer', '=', True)]")
    partner_ids = fields.Many2many(
        "res.partner",
        string="Customer",
        domain="[('customer', '=', True)]"
    )
    origin = fields.Char(string='PL Ref.')
    sale_id = fields.Many2many("sale.order", string = "SO No.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_pick', 'Waiting for pickup'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status')
    warehouse_id = fields.Many2one(comodel_name = "stock.warehouse", string = "Warehouse")
    location_id = fields.Many2one('stock.location', string = 'Source Location')
    sale_type_id = fields.Many2one(comodel_name="sale.order.type", string="Sale Type")
    user_id = fields.Many2one('res.users', string = 'Responsible')
    delivery_date_from = fields.Date("Ship Date From")
    delivery_date_to = fields.Date("Ship Date To")


class GeneratePickingListReportLine(models.TransientModel):
    _name = 'generate.picking.list.report.line'
    _description = 'Generate Picking List Report Line'

    generate_report_id = fields.Many2one(
        comodel_name='generate.picking.list.report',
        string='Report Reference',
        required=True,
        ondelete='cascade'
    )

    picking_list_id = fields.Many2one(
        comodel_name='picking.lists',
        string='Picking List',
        required=True
    )