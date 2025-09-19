from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import json

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, format_datetime


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    machines_id = fields.Many2one("mrp.machines", "Machines",)
    # machines_id = fields.Many2many('mrp.machines', required=False)
    operation_id = fields.Many2one('mrp.routing.workcenter', required=True)
    workcenter_view_id = fields.Many2one(related='operation_id.workcenter_id', readonly=True, store=True)
    mac_relate = fields.Many2many(related='operation_id.workcenter_id.machines_id', readonly=False)

    duration_expected = fields.Float(
        string = 'Expected Duration (M)', digits=(16, 2), default=60.0,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Expected duration (in minutes)")
    duration = fields.Float(
        string = 'Real Duration (M)', compute='_compute_duration', inverse='_set_duration',
        readonly=False, store=True, copy=False)
    
    partner_id = fields.Many2one('res.partner', string="Customer",tracking=True)
    
    @api.onchange("workcenter_view_id")
    def _change_workcenter_view_id(self):
        for wc in self:
            domain = []
            if not wc.workcenter_view_id.machines_id:
                wc.machines_id = False
                domain.append(('id', 'in', []))
            else:
                wc.machines_id = [(6, 0, wc.workcenter_view_id.machines_id.ids)]
                domain.append(('id', 'in', wc.workcenter_view_id.machines_id.ids))
        return {'domain': {'machines_id': domain}}
    
    def _get_duration_expected(self, alternative_workcenter=False, ratio=1):
        self.ensure_one()
        routing_id = self.env['mrp.routing'].search([('bom_id', '=', self.production_bom_id.id),('operation_ids','=',self.operation_id.id)])
        if routing_id:
            duration_expected =  (self.production_id.product_qty * routing_id.avg_produced_time)/60.0
        else:
            duration_expected = self.duration_expected
        return  duration_expected