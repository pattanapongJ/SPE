from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class RequestForMRPRequestWizard(models.TransientModel):
    _name = "request.for.mrp.request.wizard"
    _description = "Request For MRPRequest Wizard"

    name = fields.Char(string="Request For MRP Request Wizard", readonly=True, default='Request For MRP Request Wizard')
    search_id = fields.Many2one("search.forecast.purchase")
    company_id = fields.Many2one('res.company', required=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True,tracking=True)
    request_type = fields.Many2one('request.type.mr', string='Request Type', required=True, tracking=True,index=True,)
    product_type = fields.Many2one('product.type.mr', string='Product Type', required=True, tracking=True,index=True,)
    
    @api.model
    def _get_default_picking_type(self):
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        return self.env['stock.picking.type'].search([
            ('code', '=', 'mrp_operation'),
            ('warehouse_id.company_id', '=', company_id),
        ], limit=1).id
    
    @api.model
    def _get_domain_picking_do_type(self):
        addition = self.env["addition.operation.type"].search([("code", "=", "AO-06")], limit=1)
        picking_do_type_ids = self.env['stock.picking.type'].search([
            ("addition_operation_types", "=", addition.id),
        ])
        return [('id','in',picking_do_type_ids.ids)]
    
    @api.model
    def _get_default_picking_do_type(self):
        addition = self.env["addition.operation.type"].search([("code", "=", "AO-06")], limit=1)
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        return self.env['stock.picking.type'].search([
            ("addition_operation_types", "=", addition.id),
            ("warehouse_id","=",self.picking_type_id.warehouse_id.id),
            ('warehouse_id.company_id', '=', company_id),
        ], limit=1).id
    
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Factory',
        domain="[('code', '=', 'mrp_operation')]",
        default=_get_default_picking_type, check_company=True, required=True, tracking=True,)
    picking_type_do_id = fields.Many2one(
        'stock.picking.type', 'Delivery',
        domain=lambda self: self._get_domain_picking_do_type(), required=True, tracking=True,
        default=_get_default_picking_do_type, check_company=True,)

    def confirm_create_action(self):
        product_line_ids = []
        mrp_mr_model = self.env['mrp.mr']
        mrp_mr_id = mrp_mr_model.create({
            'name': 'New',
            'partner_id': self.partner_id.id,
            'request_type':self.request_type.id,
            'product_type':self.product_type.id,
            'picking_type_id':self.picking_type_id.id,
            'picking_type_do_id':self.picking_type_do_id.id,
            'department_id': self.product_type.department_id.id,
            'company_id':self.company_id.id,
            'delivery_method':"m2c",
        })
        for product_line in self.search_id.product_line_ids:
            if product_line.selected:
                line = (0, 0, {
                    'product_id': product_line.product_id.id,
                    'demand_qty': product_line.rfq_qty,
                    'uom_id': product_line.product_id.uom_id.id,
                })
                product_line_ids.append(line)
        mrp_mr_id.write({
            'product_line_ids': product_line_ids
        })      
        action = {
            'name': "Requests for MRP Request",
            'view_mode': 'form',
            'res_model': 'mrp.mr',
            'type': 'ir.actions.act_window',
            'res_id': mrp_mr_id.id,
        }
        return action