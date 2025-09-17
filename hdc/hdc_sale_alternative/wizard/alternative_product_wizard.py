from odoo import models, fields, api

class AlterNativeWizard(models.TransientModel):
    _name = 'alternative.product.wizard'
    _description = 'Alternative Product Wizard'

    internal_reference = fields.Char(string='Internal Reference', readonly=True)
    bns_code = fields.Char(string='BNS Code', readonly=True)
    name = fields.Char(string='Name', readonly=True)
    sales_price = fields.Float(string='Sales Price', readonly=True)
    on_hand = fields.Integer(string='On Hand', readonly=True)
    incoming_qty = fields.Float(string='Incoming')
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')

    default_replace_product_ids = fields.Many2many("product.product", string="Default Replace Products")

    replace_product_ids = fields.Many2one(
        'product.product',
        string='Replace Product',
        # domain="[('id', 'in', default_replace_product_ids)]"
    )
    alternative_product_ids = fields.One2many(
        'alternative.product.wizard.line','alternative_product_wizard_id',
        string='Alternative Products'
    )

    @api.onchange('replace_product_ids')
    def _onchange_replace_product_ids(self):
        alternative_lines = []
        for replace_product in self.replace_product_ids:
            alternative_lines.append((0, 0, {
                'internal_reference': replace_product.default_code,
                'bns_code': replace_product.bns_code,
                'name': replace_product.name,
                'sales_price': replace_product.lst_price,
                'on_hand': replace_product.qty_available,
                'shipping': replace_product.shipping_qty,
                'incoming_qty': replace_product.incoming_qty,
            }))

        self.alternative_product_ids = False
        self.alternative_product_ids = alternative_lines
    def replace_button(self):
        # ทำการบันทึกค่าใหม่ลงใน Sale Order Line
        # ตัวอย่างเท่านี้เท่าๆกัน คุณต้องปรับให้เหมาะสมกับโมเดล Sale Order Line ของคุณ
        sale_order_line = self.sale_order_line_id
        product_original_id = self.sale_order_line_id.product_id.id
        if self.sale_order_line_id.product_original_id.id:
            product_original_id = self.sale_order_line_id.product_original_id.id
        sale_order_line.write({
            'product_original_id': product_original_id,
            'product_id': self.replace_product_ids.id,
            'bns_code': self.replace_product_ids.bns_code,
            # 'bns_code': self.replace_product_ids.bns_code,
            # สามารถเพิ่มฟิลด์อื่นๆที่ต้องการบันทึกใน Sale Order Line ได้ตามต้องการ
        })
        sale_order_line.product_id_change()
        # else:
        #     raise exceptions.UserError('On hand must be greater than 0.')

class AlternativeProductWizardLine(models.TransientModel):
    _name = 'alternative.product.wizard.line'
    _description = 'Alternative Product Wizard Line'

    alternative_product_wizard_id = fields.Many2one('alternative.product.wizard', string='Wizard', ondelete='cascade')

    internal_reference = fields.Char(string='Internal Reference')
    bns_code = fields.Char(string='BNS Code')
    name = fields.Char(string='Name')
    sales_price = fields.Float(string='Sales Price')
    on_hand = fields.Float(string='On Hand')
    shipping = fields.Float(string='Shipping')
    incoming_qty = fields.Float(string='Incoming')
