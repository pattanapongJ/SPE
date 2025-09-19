# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'
    _description = 'Work Center Usage'

    workcenter_next_id = fields.Many2one('mrp.workcenter', 'Work Center (Next)',domain="[('id', '!=', workcenter_id),('company_id','=',company_id)]")

