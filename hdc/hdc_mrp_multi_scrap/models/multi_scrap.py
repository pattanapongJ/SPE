# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class MrpProductionInherit(models.Model):
    _inherit = 'mrp.production'

    has_multi_scrap_move = fields.Boolean('Has Multi Scrap Moves', compute = '_has_multi_scrap_move')

    def _has_multi_scrap_move(self):
        for picking in self:
            # TDE FIXME: better implementation
            picking.has_multi_scrap_move = bool(self.env['multi.stock.scrap'].search_count([('mo_id', '=', picking.id)]))

    def action_see_move_multi_scrap(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hdc_multi_scrap.action_multi_stock_scrap")
        scraps = self.env['multi.stock.scrap'].search([('mo_id', '=', self.id)])
        action['domain'] = [('id', 'in', scraps.ids)]
        action['context'] = dict(self._context, create = False)
        return action

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
                'default_user_id': self.user_id.id,
                'default_company_id': self.company_id.id, 'default_scrap_line': scrap_line,
                }, 'target': 'new',
            }
    
class MultiStockScrap(models.Model):
    _inherit = 'multi.stock.scrap'

    mo_id = fields.Many2one('mrp.production', string='Manufacturing Orders')
    mr_id = fields.Many2one('mrp.mr', string='MRP Request')