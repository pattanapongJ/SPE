from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import format_date
from datetime import datetime, timedelta


class Picking(models.Model):
    _inherit = "stock.picking"

    type_borrow = fields.Selection(
        selection=[("not_return", "เบิกไปใช้"), ("must_return", "เบิกยืมคืน")],
        string="Type Borrow",
        default="must_return",
        required=True,
    )
    team_id = fields.Many2one("crm.team", string="Sale Team")
    user_id = fields.Many2one(
        "res.users", string="Salesperson", default=lambda self: self.env.user
    )

    partner_id = fields.Many2one('res.partner', string='Customer')
    is_force_done = fields.Boolean(string="Force Done",default=False,copy=False)
    hide_return_btn = fields.Boolean(string="Hide Return Button",default=False,copy=False, compute='_compute_hide_return_btn')

    @api.onchange("type_borrow")
    def _onchange_type_borrow(self):
        if self.type_borrow == "must_return":
            self.return_date = self.borrow_date + timedelta(days=7)
        else:
            self.return_date = self.borrow_date

    def force_done(self):
        for record in self:
            result = super(Picking, record).force_done()
            record.is_force_done = True
            return result

    def _compute_hide_return_btn(self):
        for record in self:
            move_lines = record.move_ids_without_package
            hide_return_btn = False
            if all(line.return_done == line.quantity_done for line in move_lines) or record.is_force_done:
                hide_return_btn = True
            record.hide_return_btn = hide_return_btn
    
    @api.model
    def create(self, vals):
        result = super(Picking, self).create(vals)
        if result.return_date and result.borrow_date:
            if result.borrow_date > result.return_date:
                raise ValidationError(
                    _("กรุณาตรวจสอบวันที่คืนสินค้าอีกครั้ง เนื่องจากวันที่คืนสินค้าน้อยกว่าวันที่ยืม.")
                )
        return result

    def write(self, vals):
        result = super(Picking, self).write(vals)
        for rec in self:
            if rec.return_date and rec.borrow_date:
                if rec.borrow_date > rec.return_date:
                    raise ValidationError(
                        _("กรุณาตรวจสอบวันที่คืนสินค้าอีกครั้ง เนื่องจากวันที่คืนสินค้าน้อยกว่าวันที่ยืม.")
                    )
        return result

    def button_validate(self):
        res = super(Picking, self).button_validate()
        for record in self:
            if record.request_spare_parts_type == True:
                if record.type_borrow == "not_return":
                    record.force_done()
        return res
