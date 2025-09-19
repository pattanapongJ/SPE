from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import json

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, format_datetime


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    is_user_working_check = fields.Boolean(default=False)
    is_check_start = fields.Boolean(default=False,copy=False)

    def button_pending(self):
        workorder_ids = self.env["mrp.workorder"].search([("machines_id", "=", self.machines_id.id)])
        for rec in workorder_ids:
            rec.is_check_start = False
            rec.end_previous()
        return True

    def button_unblock2(self):
        workorder_ids = self.env["mrp.workorder"].search([("machines_id", "=", self.machines_id.id)])
        for rec in workorder_ids:
            rec.is_user_working_check = False
            rec.is_check_start = False
        return True

    def button_start(self):
        self.ensure_one()
        self.is_check_start = True

        if any(not time.date_end for time in self.time_ids.filtered(lambda t: t.user_id.id == self.env.user.id)):
            return True
        # As button_start is automatically called in the new view
        if self.state in ('done', 'cancel'):
            return True

        if self.product_tracking == 'serial':
            self.qty_producing = 1.0
        elif self.qty_producing == 0:
            self.qty_producing = self.qty_remaining

        self.env['mrp.workcenter.productivity'].create(
            self._prepare_timeline_vals(self.duration, datetime.now())
        )
        if self.production_id.state != 'progress':
            self.production_id.write({
                'date_start': datetime.now(),
            })
        if self.state == 'progress':
            return True
        start_date = datetime.now()
        vals = {
            'state': 'progress',
            'date_start': start_date,
        }
        if not self.leave_id:
            leave = self.env['resource.calendar.leaves'].create({
                'name': self.display_name,
                'calendar_id': self.workcenter_id.resource_calendar_id.id,
                'date_from': start_date,
                'date_to': start_date + relativedelta(minutes=self.duration_expected),
                'resource_id': self.workcenter_id.resource_id.id,
                'time_type': 'other'
            })
            vals['leave_id'] = leave.id
            return self.write(vals)
        else:
            if not self.date_planned_start or self.date_planned_start > start_date:
                vals['date_planned_start'] = start_date
                vals['date_planned_finished'] = self._calculate_date_planned_finished(start_date)
            if self.date_planned_finished and self.date_planned_finished < start_date:
                vals['date_planned_finished'] = start_date
            return self.with_context(bypass_duration_calculation=True).write(vals)

    def button_finish(self):
        end_date = datetime.now()
        for workorder in self:
            workorder.is_check_start = True
            if workorder.state in ('done', 'cancel'):
                continue
            workorder.end_all()
            vals = {
                'qty_produced': workorder.qty_produced or workorder.qty_producing or workorder.qty_production,
                'state': 'done',
                'date_finished': end_date,
                'date_planned_finished': end_date
            }
            if not workorder.date_start:
                vals['date_start'] = end_date
            if not workorder.date_planned_start or end_date < workorder.date_planned_start:
                vals['date_planned_start'] = end_date
            workorder.with_context(bypass_duration_calculation=True).write(vals)

            workorder._start_nextworkorder()
        return True
