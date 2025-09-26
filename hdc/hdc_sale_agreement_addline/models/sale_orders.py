
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError,UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_sale_ok3(self):
        if self.is_from_agreement:
            for line in self.order_line:
                if line.product_id.free_product and not line.blanket_order_line and not line.free_product and line.product_id.type != 'service':
                    wizard = self.env['sale.order.confirm.addline.wizard'].create({
                        'message': _("กรุณาตรวจสอบรายการสินค้าอีกครั้ง ระบบพบข้อมูลรายการถูกเพิ่มนอกจากรายการที่ทำสัญญา หากท่ายืนยันระบบจะมีการคำนวนราคาใหม่ หากไม่ยืนยันกรุณาตรวจสอบว่าดำเนินการระบุสินค้าเพิ่มใหม่เป็นสินค้าฟรีแล้วหรือยัง"),
                        'order_id': self.id,
                    })
                    action = self.env["ir.actions.actions"]._for_xml_id("hdc_sale_agreement_addline.action_sale_order_confirm_addline_wizard")
                    action['views'] = [(self.env.ref('hdc_sale_agreement_addline.view_sale_order_confirmation_wizard_form').id, 'form')]
                    action['name'] = _('User Error')
                    action['res_model'] = 'sale.order.confirm.addline.wizard'
                    action['target'] = 'new'
                    action['res_id'] = wizard.id
                    return action
                    # return {
                    #     'type': 'ir.actions.act_window',
                    #     'name': _('User Error'),
                    #     'res_model': 'sale.order.confirm.addline.wizard',
                    #     'view_mode': 'form',
                    #     'target': 'new',
                    #     'res_id': wizard.id,
                    # }
        return super(SaleOrder, self).action_sale_ok2()
