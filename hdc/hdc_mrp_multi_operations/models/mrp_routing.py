# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    routing_ids = fields.One2many('mrp.routing', 'bom_id', 'Operations', copy = True)

    operation_ids = fields.One2many('mrp.routing.workcenter', compute='_compute_routing_ids')

    @api.depends('routing_ids')
    def _compute_routing_ids(self):
        for bom_line in self:
            add_operation_ids = []
            if bom_line.routing_ids:
                for line in bom_line.routing_ids:
                    if line.operation_ids:
                        add_operation_ids.append(line.operation_ids.id)
                if add_operation_ids:
                    bom_line.write({"operation_ids": add_operation_ids})
                else:
                    bom_line.write({"operation_ids": False})
            else:
                bom_line.write({"operation_ids": False})

class MrpRouting(models.Model):
    """ Specifies routings of work centers """
    _name = 'mrp.routing'
    _description = 'Routings'

    operation_ids = fields.Many2one('mrp.routing.workcenter')
    name = fields.Char(related='operation_ids.name')
    avg_produced_time = fields.Float(string="Avg Produced (s/pcs)")
    time_cycle = fields.Float(related='operation_ids.time_cycle')
    workcenter_id = fields.Many2one(related='operation_ids.workcenter_id')
    bom_id = fields.Many2one('mrp.bom', 'Parent BoM', index = True, ondelete = 'cascade', invisible=True)

