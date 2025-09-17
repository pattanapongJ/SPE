# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta, datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class MrpProductionInherit(models.Model):
    _inherit = 'mrp.production'

    def action_open_wizard_mrp_create_pr(self):
        mo_line = []
        for mo in self.move_raw_ids:
            mo_line.append((0, 0, {
                'product_id': mo.product_id.id,
                'product_qty': mo.product_uom_qty,
                'estimated_cost': 0.0,
            }))
        
        context = {
            'default_mo_id': self.id,
            'default_location_id': self.location_src_id.id,
            'default_location_dest_id': self.location_dest_id.id,
            'default_order_line_ids': mo_line,
        }
        if self.picking_type_id.request_type:
            request_type = self.picking_type_id.request_type
            context['default_request_type'] = request_type.id
            if request_type.currency_id:
                context['default_currency_id'] = request_type.currency_id.id
                
        return {
                'type': 'ir.actions.act_window',
                'name': 'Create PR',
                'res_model': 'wizard.mrp.create.pr',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }

    create_pr_count = fields.Integer(
        "Count of generated PR",
        compute='_compute_create_pr_count')

    def _compute_create_pr_count(self):
        for production in self:
            origin = production.name
            production.create_pr_count = self.env['purchase.request'].search_count([('origin', '=', origin),("is_create_pr", "=", True)])

    def action_view_create_pr(self):
        self.ensure_one()
        purchase_request_ids = self.env['purchase.request'].search([('origin', '=', self.name),("is_create_pr", "=", True)]).ids
        action = {
            'res_model': 'purchase.request',
            'type': 'ir.actions.act_window',
        }
        if len(purchase_request_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': purchase_request_ids[0],
            })
        else:
            action.update({
                'name': _("Purchase Request generated from %s", self.name),
                'domain': [('id', 'in', purchase_request_ids)],
                'view_mode': 'tree,form',
            })
        return action
        