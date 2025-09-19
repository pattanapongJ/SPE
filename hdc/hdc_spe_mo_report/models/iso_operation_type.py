from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import time, datetime, timedelta



class IsoOperationType(models.Model):
    _name = 'iso.operation.type'
    _description = 'ISO Operation Type'

    name = fields.Char(string='Name')
    product_produce_type = fields.Many2one(comodel_name='product.type.mr', string='Product Type', index=True)
    doc_name = fields.Selection([
        ("material_requestion", "ใบเบิก/ขอเบิก"),
        ("material_requestion_cutting", "ใบเบิก/ตัดวัตถุดิบ"),
        ("mrp_production_state", "ใบรายงานสถานะการผลิต"),
        ("mrp_fg_ls", "ใบรับผลิตเสร็จ"),
        ("mrp_production_order", "ใบสั่งผลิต"),
    ],string="Doc Name")
    iso_number = fields.Char(string='ISO Number',copy=False)
    operation_type_id = fields.Many2one(comodel_name='stock.picking.type', string='Operation Type', index=True)
    
    @api.onchange('doc_name', 'iso_number')
    def _onchange_product_produce_type(self):
        # if self.product_produce_type:
        doc_name = self.doc_name
        if self.doc_name == "material_requestion":
            doc_name = "ใบเบิก/ขอเบิก"
        elif self.doc_name == "material_requestion_cutting":
            doc_name = "ใบเบิก/ตัดวัตถุดิบ"
        elif self.doc_name == "mrp_production_state":
            doc_name = "ใบรายงานสถานะการผลิต"
        elif self.doc_name == "mrp_production_order":
            doc_name = "ใบสั่งผลิต"
        elif self.doc_name == "mrp_fg_ls":
            doc_name = "ใบรับผลิตเสร็จ"
        # self.name = "[{}] {} ({})".format(self.product_produce_type.name, doc_name, self.iso_number)
        self.name = " {} ({})".format(doc_name, self.iso_number)

    
# class ProductProduceType(models.Model):
#     _name = 'product.produce.type'
#     _description = 'Product Produce Type'

#     name = fields.Char(string='Product Produce Type', index=True)
