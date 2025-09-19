# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ReSupplyDeliveryScheduleMaster(models.Model):
    _name = "resupply.delivery.schedule.master"
    _description = "Resupply Delivery Schedule Master"

    name = fields.Char(string="Delivery Schedule", required=True)
    warehouse_selection = fields.Selection([
        ('distribution_center','Distribution Center'),
        ('branch','Branch'),
    ],string="Warehouse", required=True, default='branch')
    branch_id = fields.Many2one('res.branch',string="Branch")
    delivery_round_id = fields.Many2one('delivery.round',string="Delivery Round")
    status_active = fields.Boolean(string="Online", default=True, required=True)
    max_weight = fields.Float(string='Max Weight', digits=(16, 2), required=True)
    min_weight = fields.Float(string='Min Weight', digits=(16, 2), required=True)

    location_line_ids = fields.One2many('resupply.location.tab', 'location_line_id', string='Location')

    @api.onchange('warehouse_selection')
    def warehouse_onchange(self):
        if self.warehouse_selection == "distribution_center" :
            self.branch_id = False

class ReSupplyLocationTab(models.Model):
    _name = "resupply.location.tab"
    _description = "Resupply Location Tab"

    location_line_id = fields.Many2one('resupply.delivery.schedule.master')
    location_id = fields.Many2one('stock.location', string='Location', required=True)
    delivery_start_time = fields.Float(string='Delivery Start Time', digits=(16, 2), required=True)
    delivery_end_time = fields.Float(string='Delivery End Time', digits=(16, 2), required=True)

