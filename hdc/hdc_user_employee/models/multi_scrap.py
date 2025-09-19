# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class MultiStockScrap(models.Model):
    _inherit = 'multi.stock.scrap'

    user_id = fields.Many2one("res.users", string = "Responsible user")
    user_employee_id = fields.Many2one('hr.employee', string = 'Responsible',domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

class Picking(models.Model):
    _inherit = "stock.picking"

    def button_multi_scrap(self):
        self.ensure_one()
        view = self.env.ref('hdc_multi_scrap.multi_stock_scrap_form_view2')
        products = self.env['product.product']
        scrap_line = []
        for move in self.move_ids_without_package:
            if move.state not in ('draft', 'cancel') and move.product_id.type in ('product', 'consu'):
                products |= move.product_id
                scrap_line.append([0,0, {
                    "product_id": move.product_id.id,
                    "product_uom_id": move.product_uom.id
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
                'default_origin': self.name, 'default_picking_id': self.id,
                'default_partner_id': self.partner_id.id, 'default_user_id': self.user_id.id,'default_user_employee_id': user_employee_id,
                'default_company_id': self.company_id.id, 'default_scrap_line': scrap_line,
                }, 'target': 'new',
            }
    
class MrpProductionInherit(models.Model):
    _inherit = 'mrp.production'

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
        for move in self.move_raw_ids:
            if move.state not in ('draft', 'cancel') and move.product_id.type in ('product', 'consu'):
                products |= move.product_id
                scrap_line.append([0,0, {
                    "product_id": move.product_id.id,
                    "product_uom_id": move.product_uom.id
                    }])
                
        user_employee_id = self.search_employee()

        return {
            'name': _('Multi Scrap Orders'),
            'view_mode': 'form',
            'res_model': 'multi.stock.scrap',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            # 'default_partner_id': self.partner_id.id, 
            'context': {
                'default_origin': self.name, 'default_mo_id': self.id,
                'default_user_id': self.user_id.id,'default_user_employee_id': user_employee_id,
                'default_company_id': self.company_id.id, 'default_scrap_line': scrap_line,
                }, 'target': 'new',
            }