from odoo import models, fields

class ProductImageAngle(models.Model):
    _name = 'product.image.angle'
    _description = 'Product Image Angle'
    _order = 'sequence, id'

    name = fields.Char("Image Name")
    image_1920 = fields.Image("Image", required=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', ondelete='cascade')
    # angle = fields.Selection([
    #     ('front', 'ด้านหน้า'),
    #     ('back', 'ด้านหลัง'),
    #     ('side', 'ด้านข้าง'),
    #     ('top', 'ด้านบน'),
    #     ('bottom', 'ด้านล่าง'),
    #     ('other', 'อื่น ๆ'),
    # ], string="มุมมอง", required=True)
    note = fields.Char("หมายเหตุเพิ่มเติม")
    sequence = fields.Integer("ลำดับ", default=10)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_angle_ids = fields.One2many('product.image.angle', 'product_tmpl_id', string="รูปหลายมุม")