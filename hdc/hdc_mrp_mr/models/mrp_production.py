# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    mr_id = fields.Many2one('mrp.mr', string='MR')
    mr_count = fields.Integer(compute="_compute_mr_count", string="Number of Manufacturing",tracking=True,)
    product_line_modify_id = fields.Many2one(
        comodel_name="mr.product.list.modify.line",
        string="Product modify line",
    )
    def write(self, vals):
        res = super(MrpProduction, self).write(vals)
        for rec in self:
            if rec.mr_id and (rec.state == 'done' or vals.get('state',False)=='done'):
                if rec.mr_id.is_modify == False:
                    rec.mr_id._compute_product_line_ids()
                elif rec.mr_id.is_modify == True:
                    rec.mr_id._compute_product_line_modify_ids()
        return res

    def _compute_mr_count(self):
        if self.mr_id :
            self.mr_count = 1
        else :
            self.mr_count = 0

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
            
        if self.bom_id:
            self._create_workorder()
        else:
            self.workorder_ids = False

    @api.constrains('product_id', 'move_raw_ids')
    def _check_production_lines(self):
        for production in self:
            if production.mr_id.is_modify == False:
                for move in production.move_raw_ids:
                    if production.product_id == move.product_id:
                        raise ValidationError(_("The component %s should not be the same as the product to produce.") % production.product_id.display_name)

    def action_cancel(self):
        for rec in self:
            if rec.state == 'progress':
                attachment_id = self.env['ir.attachment'].search([('res_model', '=', 'mrp.production'),('res_id', '=', self.id)])
                if not attachment_id:
                    raise ValidationError(_("กรุณาแนบเอกสารอนุมัติ"))
            super(MrpProduction, self).action_cancel()

    def action_create_rework(self):
        for rec in self:
            new_rec = rec.copy({
                'origin': rec.name,
            })
            return {
                'type': 'ir.actions.act_window',
                'res_model': rec._name,
                'view_mode': 'form',
                'res_id': new_rec.id,
                'target': 'current',
            }