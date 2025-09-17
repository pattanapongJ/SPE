
from datetime import date, timedelta
from unittest import skip

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError,UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_from_agreement = fields.Boolean('is_from_agreement',default=False,copy=False)
    def action_sale_ok3(self):
        if self.is_from_agreement:
            for line in self.order_line:
                if line.product_id.free_product and not line.blanket_order_line and not line.free_product:
                    wizard = self.env['sale.order.confirm.addline.wizard'].create({
                        'message': _("กรุณาตรวจสอบรายการสินค้าอีกครั้ง ระบบพบข้อมูลรายการถูกเพิ่มนอกจากรายการที่ทำสัญญา หากท่ายืนยันระบบจะมีการคำนวนราคาใหม่ หากไม่ยืนยันกรุณาตรวจสอบว่าดำเนินการระบุสินค้าเพิ่มใหม่เป็นสินค้าฟรีแล้วหรือยัง"),
                        'order_id': self.id,
                    })

                    return {
                        'type': 'ir.actions.act_window',
                        'name': _('User Error'),
                        'res_model': 'sale.order.confirm.addline.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'res_id': wizard.id,
                    }
                    
        return super().action_sale_ok2()
    

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_product_domain(self):
        """ ฟังก์ชันกำหนด domain ตามค่า is_from_agreement """
        if self.order_id and self.order_id.is_from_agreement:
            return [('type', '=', 'service')]
        return [('sale_ok', '=', True)]
    return_delivery_qty = fields.Float(string='Return Delivery QTY', digits="Product Unit of Measure", default=0.00) 
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain=lambda self: self._get_product_domain(),
    )

    # @api.onchange('product_id')
    # def _onchange_domain_product_id(self):
    #     for line in self:
    #         if line.order_id and line.order_id.is_from_agreement:
    #             return {
    #                 'domain': {'product_id': [('type', '=', 'service')]}
    #             }
    #         else:
    #             return {
    #                 'domain': {'product_id': [('sale_ok', '=', True)]} 
    #             }
    # def get_assigned_bo_line(self):
    #     self.ensure_one()
    #     eligible_bo_lines = self._get_eligible_bo_lines()
    #     if eligible_bo_lines:
    #         if (
    #             self.blanket_order_line
    #             and self.blanket_order_line not in eligible_bo_lines
    #         ):
    #             self.blanket_order_line = self._get_assigned_bo_line(eligible_bo_lines)
    #     else:
    #         self.blanket_order_line = False
    #     return {"domain": {"blanket_order_line": [("id", "in", eligible_bo_lines.ids)]}}

    # def write(self, vals):
    #     user_error = False
    #     if self.blanket_order_line:
    #         if vals.get("product_uom_qty"):
    #             now_remain = self.blanket_order_line.remaining_uom_qty
    #             now_remain += self.product_uom_qty
    #             now_remain -= vals.get("product_uom_qty")
    #             if now_remain < 0 :
    #                 user_error = True
    #             else:
    #                 if vals.get("blanket_order_line") is False:
    #                     vals.pop("blanket_order_line")
    #     res = super().write(vals)
    #     if self.blanket_order_line:
    #         for rec in self :
    #             now_remain = rec.blanket_order_line.remaining_uom_qty
    #             if now_remain < 0 :
    #                     user_error = True
    #             if user_error:
    #                 raise UserError(
    #                             _("ไม่สามารถแก้ไขจำนวน Demand มากกว่าที่กำหนดในสัญญาได้")
    #                         )

    #     return res