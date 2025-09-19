# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools.misc import clean_context

class MRPMR(models.Model):
    _inherit = 'mrp.mr'

    has_multi_scrap_move = fields.Boolean('Has Multi Scrap Moves', compute = '_has_multi_scrap_move')
    hide_btn_multi_scrap = fields.Boolean(compute="_compute_btn_multi_scrap", string="Hide Multi Scrap")

    def _compute_btn_multi_scrap(self):
        for mr in self:
            mr.hide_btn_multi_scrap = False
            if mr.request_type.is_claim == True:
                if mr.state == "cancel":
                    mr.hide_btn_multi_scrap = True
                else:
                    mr.hide_btn_multi_scrap = False
            else:
                mr.hide_btn_multi_scrap = True

    def _has_multi_scrap_move(self):
        for picking in self:
            # TDE FIXME: better implementation
            picking.has_multi_scrap_move = bool(self.env['multi.stock.scrap'].search_count([('mr_id', '=', picking.id)]))

    def action_see_move_multi_scrap(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hdc_multi_scrap.action_multi_stock_scrap")
        scraps = self.env['multi.stock.scrap'].search([('mr_id', '=', self.id)])
        action['domain'] = [('id', 'in', scraps.ids)]
        action['context'] = dict(self._context, create = False)
        return action

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
        return {
            'name': _('Multi Scrap Orders'),
            'view_mode': 'form',
            'res_model': 'multi.stock.scrap',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',

            'context': {
                'default_origin': self.name, 'default_mr_id': self.id,
                'default_user_id': self.env.user.id,
                'default_company_id': self.company_id.id, 'default_scrap_line': scrap_line,
                'default_location_id': self.picking_type_id.default_location_dest_id.id,
                'default_scrap_location_id': self.product_type.scrap_location.id
                }, 'target': 'new',
            }