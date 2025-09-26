from odoo import api, fields, models, _

class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    workorder_id_wizard = fields.Many2one('mrp.workorder', 'Work Order', check_company=True)
    is_user_working_check = fields.Boolean(default=False)
    machines_id = fields.Many2one('mrp.machines', required=False)

    def button_block2(self):
        self.ensure_one()
        workorder_ids = self.env["mrp.workorder"].search([("machines_id", "=", self.machines_id.id)])
        for rec in workorder_ids:
            rec.end_previous()
            rec.is_user_working_check = True
            rec.is_check_start = True
        self.unlink()

    