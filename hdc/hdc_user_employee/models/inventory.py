from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Inventory(models.Model):
    _inherit = "stock.inventory"
    
    # Fields for warehouse confirmation
    user_confirm_picking = fields.Char(string="Confirmed Inventory user", readonly=True,copy=False, tracking=True)
    user_employee_confirm_picking = fields.Many2one('hr.employee',string='Confirmed Inventory', readonly=True,copy=False, tracking=True)

    # Fields for inventory adjustment confirmation
    user_validation_picking = fields.Char(string="Validate Warehouse user", readonly=True, tracking=True,copy=False)
    user_employee_validation_picking = fields.Many2one('hr.employee',string='Validate Warehouse', readonly=True, tracking=True,copy=False)

    def search_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id
        
    def action_confirm_adjustment(self):
        self.btn_status = 'inventory'
        if not self.confirm_picking_date:
            self.confirm_picking_date = fields.Datetime.now()
        self.user_confirm_picking = self.env.user.name
        self.user_employee_confirm_picking = self.search_employee()

    def action_validate(self):
        result = super(Inventory, self).action_validate()
        if not self.validation_picking_date:
            self.validation_picking_date = fields.Datetime.now()
        self.user_validation_picking = self.env.user.name
        self.user_employee_validation_picking = self.search_employee()
        self.btn_status = 'done'
        
        return result
