from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Inventory(models.Model):
    _inherit = "stock.inventory"

    btn_status = fields.Selection([('warehouse', 'Warehouse'),('inventory', 'Inventory'),('done','Done')],
                                        default='warehouse', string='Inventory Status',copy=False)
    
    # Fields for warehouse confirmation
    warehouse_status = fields.Selection([('warehouse', 'Inprogress'),('done','Done'),('cancel','Cancelled')],
                                        default='warehouse', string='Inventory Status',copy=False,compute='_compute_access_right_value',)
    confirm_picking_date = fields.Datetime(string="Confirmed Inventory Date",copy=False, tracking=True)
    user_confirm_picking = fields.Char(string="Confirmed Inventory", readonly=True,copy=False, tracking=True)

    # Fields for inventory adjustment confirmation
    validation_picking_date = fields.Datetime(string="Validate Warehouse Date", tracking=True,copy=False)
    user_validation_picking = fields.Char(string="Validate Warehouse", readonly=True, tracking=True,copy=False)
    inventory_status = fields.Selection([('waiting', 'Waiting Confirm'),('progress', 'In Progress'),('done','Done'),('cancel','Cancelled')],
                                        default='waiting', string='Warehouse Status',copy=False,compute='_compute_access_right_value',)

    def action_confirm_adjustment(self):
        self.btn_status = 'inventory'
        if not self.confirm_picking_date:
            self.confirm_picking_date = fields.Datetime.now()
        self.user_confirm_picking = self.env.user.name


    @api.onchange('state')
    def _onchange_state_adj(self):
        for rec in self:
            if rec.state == 'done':
                rec.inventory_status = 'done'

    def _compute_access_right_value(self):
        for record in self:
            if record.state in ['draft','confirm'] :
                if record.btn_status == 'inventory':
                    record.warehouse_status = 'done'
                    record.inventory_status = 'progress'
                else:
                    record.warehouse_status = 'warehouse'
                    record.inventory_status = 'waiting'
            elif record.state == 'done':
                record.warehouse_status = 'done'
                record.inventory_status = 'done'
            else:
                record.warehouse_status = "cancel"
                record.inventory_status = "cancel"

    def action_validate(self):
        result = super(Inventory, self).action_validate()
        if not self.validation_picking_date:
            self.validation_picking_date = fields.Datetime.now()
        self.user_validation_picking = self.env.user.name
        self.btn_status = 'done'
        
        return result
    
    def action_cancel_draft(self):
        result = super(Inventory, self).action_cancel_draft()
        self.btn_status = 'warehouse'
        
        return result
    
