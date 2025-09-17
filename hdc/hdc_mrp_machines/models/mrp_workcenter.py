from odoo import api, fields, models, _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    # machines_id = fields.Many2one('mrp.machines', required=False)
    machines_id = fields.Many2many('mrp.machines', required=False)

        


    