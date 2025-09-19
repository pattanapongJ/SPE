# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import MissingError, UserError, ValidationError



class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    remark = fields.Char(string="Remark")

class Inventory(models.Model):
    _inherit = 'stock.inventory'

    noted = fields.Text(string="Noted")
    sequence = fields.Char(string="Sequence", default = 'New', readonly=True)
    type_action = fields.Selection(selection=[("count_stock", "ตรวจนับ"), ("edit_stock", "ปรับปรุงสต๊อก")], string="Type", default="count_stock")
    operation_types = fields.Many2one('stock.picking.type', string='Operations Types')

    #ไปไว้ที่ inventory_adj_type_master
    # @api.model
    # def create(self, vals):
    #     sequence = vals.get('sequence', 'New')
    #     if sequence:
    #         vals['sequence'] = self.env['ir.sequence'].next_by_code('inventory_adjustment') or _('New')

    #     result = super(Inventory, self).create(vals)
    #     return result
    
class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    @api.depends('product_qty', 'theoretical_qty')
    def _compute_difference(self):
        for line in self:
            if line.type_action == 'count_stock':
                line.difference_qty = line.product_qty - line.theoretical_qty
            if line.type_action == 'edit_stock':
                line.difference_qty = line.theoretical_qty  - line.product_qty

    remark = fields.Char(string="Remark")

    type_action = fields.Selection(related='inventory_id.type_action', string="Type", store=True)

    inventory_adjust = fields.Char(string="Ajd +/-")

    @api.onchange('inventory_adjust')
    def _onchange_inventory_adjust(self):
        self._apply_inventory_adjust()

    def _apply_inventory_adjust(self):
        for rec in self:
            if rec.inventory_adjust:
                try:
                    if rec.inventory_adjust[0] == '+':
                        number = int(rec.inventory_adjust[1:])
                        rec.theoretical_qty = rec.theoretical_qty + number
                        rec.inventory_adjust = ''
                    elif rec.inventory_adjust[0] == '-':
                        number = int(rec.inventory_adjust[1:])
                        rec.theoretical_qty = rec.theoretical_qty - number
                        rec.inventory_adjust = ''
                    else:
                        raise UserError('ในช่อง Adj +/- กรุณากรอกเครื่องหมายแล้วตามด้วยตัวเลข ตัวอย่าง +10, -100, +20, +250')
                except Exception:
                    raise UserError('ในช่อง Adj +/- กรุณากรอกเครื่องหมายแล้วตามด้วยตัวเลข ตัวอย่าง +10, -100, +20, +250')


    def _get_move_values(self, qty, location_id, location_dest_id, out):
        res = super()._get_move_values(qty, location_id, location_dest_id, out)
        self.ensure_one()

        if res.get('move_line_ids'):
            # เพิ่ม remark เข้า move_line_ids ตัวแรก (หรือหลายตัวถ้ามีหลายบรรทัด)
            new_lines = []
            for move_line in res['move_line_ids']:
                line_data = move_line[2]
                line_data['remark'] = self.remark
                new_lines.append((0, 0, line_data))
            res['move_line_ids'] = new_lines

        return res

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        rec._apply_inventory_adjust()
        return rec

    def write(self, vals):
        res = super().write(vals)
        self._apply_inventory_adjust()
        return res