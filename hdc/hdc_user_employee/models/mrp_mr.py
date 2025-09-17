# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools.misc import clean_context

class MRPMR(models.Model):
    _inherit = 'mrp.mr'

    def _default_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id
    
    sale_person = fields.Many2one('res.users', string='Sale Person user', tracking=False,)
    sale_person_employee = fields.Many2one('hr.employee', string='Sale Person', tracking=True,)
    user_request = fields.Many2one('res.users', string='Request user', default=lambda self: self.env.user, tracking=False,index=True,)
    user_request_employee = fields.Many2one('hr.employee', string='Request', default=lambda self: self._default_employee(), tracking=True,index=True,)
    
    def search_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id
    
    def button_multi_scrap(self):
        self.ensure_one()
        view = self.env.ref('hdc_multi_scrap.multi_stock_scrap_form_view2')
        products = self.env['product.product']
        scrap_line = []
        for line in self.product_line_ids:
            scrap_line.append([0,0, {
                "product_id": line.product_id.id,
                "product_uom_id": line.product_id.uom_id.id
                }])
            
        user_employee_id = self.search_employee()

        return {
            'name': _('Multi Scrap Orders'),
            'view_mode': 'form',
            'res_model': 'multi.stock.scrap',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',

            'context': {
                'default_origin': self.name, 'default_mr_id': self.id,
                'default_user_id': self.env.user.id,'default_user_employee_id': user_employee_id,
                'default_company_id': self.company_id.id, 'default_scrap_line': scrap_line,
                'default_location_id': self.picking_type_id.default_location_dest_id.id,
                'default_scrap_location_id': self.product_type.scrap_location.id
                }, 'target': 'new',
            }
    
    # Sale Person
    @api.onchange("sale_person_employee")
    def _onchange_sale_person_employee(self):
        if self.sale_person_employee.user_id:
            self.sale_person = self.sale_person_employee.user_id

    # Request
    @api.onchange("user_request_employee")
    def _onchange_user_request_employee(self):
        if self.user_request_employee.user_id:
            self.user_request = self.user_request_employee.user_id