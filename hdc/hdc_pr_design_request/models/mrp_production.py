# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    mr_id = fields.Many2one('mrp.mr', string='MR')
    mr_count = fields.Integer(compute="_compute_mr_count", string="Number of Manufacturing",tracking=True,)

    def _compute_mr_count(self):
        if self.mr_id :
            self.mr_count = 1

    def action_mr_ids(self):
        mo_ids = self.env['mrp.mr'].search([('id', '=', self.mr_id.id)],limit=1)
        action = {
            'res_model': 'mrp.mr',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': mo_ids.id,
        }
        return action
    

    def reset_bom_id(self,demand_qty):
        if not self.bom_id and not self._origin.product_id:
            return
        # Clear move raws if we are changing the product. In case of creation (self._origin is empty),
        # we need to avoid keeping incorrect lines, so clearing is necessary too.
        if self.product_id != self._origin.product_id:
            self.move_raw_ids = [(5,)]
        if self.bom_id and self.product_qty > 0:
            # keep manual entries
            list_move_raw = [(4, move.id) for move in self.move_raw_ids.filtered(lambda m: not m.bom_line_id)]
            moves_raw_values = self._get_moves_raw_values()
            move_raw_dict = {move.bom_line_id.id: move for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)}
            for move_raw_values in moves_raw_values:
                if move_raw_values['bom_line_id'] in move_raw_dict:
                    # update existing entries
                    list_move_raw += [(1, move_raw_dict[move_raw_values['bom_line_id']].id, move_raw_values)]
                else:
                    # add new entries
                    list_move_raw += [(0, 0, move_raw_values)]
            self.move_raw_ids = list_move_raw
        else:
            self.move_raw_ids = [(2, move.id) for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)]

        if self.product_id and self.product_qty > 0:
            self._create_update_move_finished()
        else:
            self.move_finished_ids = [(2, move.id) for move in self.move_finished_ids.filtered(lambda m: m.bom_line_id)]
            

    def write(self, vals):
        res = super(MrpProduction, self).write(vals)
        if self.mr_id and self.mr_id.state == 'approved':
            self.mr_id.write({'state': 'in_progress'})
        if 'product_qty' in vals:
            for production in self:
                if production.mr_id:
                    for product_line in production.mr_id.product_line_ids:
                        mr_line = production.env['mr.product.list.line'].search([
                            ('mr_id', '=', production.mr_id.id),
                            ('product_id', '=', product_line.product_id.id)
                        ])
                        if mr_line:
                            mr_line.write({'produced_qty': vals['product_qty']})
        return res
