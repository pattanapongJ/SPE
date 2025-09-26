
from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'priority desc, id desc'

    is_return_request = fields.Boolean(
        string='Has Return Request',
        compute='_compute_return_request_flag',
        store=True
    )

    customer_requisition = fields.Char(string='Customer Requisition')

    @api.depends('origin')
    def _compute_return_request_flag(self):
        for picking in self:
            count = self.env['customer.return.request'].search_count([
                ("name", "=", picking.origin)
            ])
            picking.is_return_request = bool(count)

    def do_crr_return_customer_print(self):
        return self.env.ref('hdc_rma_multi.crr_return_customer_report').report_action(self)
        
    def print_crr_list(self):
        self.ensure_one()
        return {
                "name": "Report RMA",
                "type": "ir.actions.act_window",
                "res_model": "wizard.crr.report.list",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.state,
                            "default_picking_id": self.id},
            }