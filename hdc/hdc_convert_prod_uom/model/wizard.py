# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class FixDefaultUomWizard(models.TransientModel):
    _name = 'fix.default.uom.wizard'
    _description = 'Fix Default UOM Wizard'

    product_ids = fields.Many2many(
        'product.template',
        string='Products',
        required=True,
        help='Select products to fix default UOM'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default products from context"""
        res = super().default_get(fields_list)
        if 'product_ids' in fields_list:
            active_ids = self.env.context.get('active_ids', [])
            if active_ids:
                # ตรวจสอบว่าสินค้ามี UOM หรือไม่
                products = self.env['product.template'].browse(active_ids).filtered(lambda p: p.uom_id)
                if products:
                    res['product_ids'] = [(6, 0, products.ids)]
        return res

    def action_fix_default_uom(self):
        """Fix default UOM for selected products"""
        if not self.product_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'ไม่พบสินค้า',
                    'message': 'กรุณาเลือกสินค้าที่ต้องการแก้ไข',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # เรียกใช้ method fix_existing_default_uom_data
        return self.product_ids.fix_existing_default_uom_data()
