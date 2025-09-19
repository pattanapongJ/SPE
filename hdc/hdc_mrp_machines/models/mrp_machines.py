from odoo import api, fields, models

class MrpMachines(models.Model):
    _name = 'mrp.machines'
    _description = 'MRP Machines'

    name = fields.Char(string= "Machines Name", required=True)
    workcenter_id = fields.Many2one("mrp.workcenter", "Work Center")
    capacity = fields.Char(string="Capacity/Hours")
    active = fields.Boolean(default = True)


    def preview_workorder(self):
        self.ensure_one()
        tree_view = self.env.ref("hdc_mrp_machines.mrp_production_workorder_tree_view", raise_if_not_found = False)
        name_action = "Work Orders"
        lang_code = self.env.context.get("lang") or False
        if lang_code == "th_TH":
            name_action = "คำสั่งงาน"
        action = {
            "type": "ir.actions.act_window",
            "name": name_action,
            "res_model": "mrp.workorder",
            "view_mode": "tree",
            "search_view_id": [self.env.ref('mrp.view_mrp_production_workorder_form_view_filter').id, 'search'],
            "context": {'search_default_date': True},
            "domain": [("machines_id", "=", self.id)],
            }
        if tree_view:
            action["views"] = [(tree_view.id, "tree")]
        return action
        