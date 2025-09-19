from odoo import fields, models, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit ='sale.order'

    order_bom_line = fields.One2many(
        "sale.bom.line",
        "order_id",
        string="Components",
        compute="_compute_order_bom_line",
        store=True,
    )

    @api.depends("order_line.product_id", "order_line.product_uom_qty")
    def _compute_order_bom_line(self):
        for order in self:
            bom_lines = []
            for line in order.order_line:
                if not line.product_id:
                    continue
                    
                bom = self.env['mrp.bom']._bom_find(product=line.product_id, company_id=order.company_id.id)
                
                if bom and bom.type == 'phantom':
                    for bom_line in bom.bom_line_ids:
                        bom_lines.append((0, 0, {
                            'origin_product_id': line.product_id.id,
                            'product_id': bom_line.product_id.id,
                            'product_uom_qty': bom_line.product_qty * line.product_uom_qty,
                            'product_uom': bom_line.product_uom_id.id,
                        }))
                else:
                    bom_lines.append((0, 0, {
                        'origin_product_id': line.product_id.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                    }))
            
            order.order_bom_line = [(5, 0, 0)] + bom_lines

class SaleOrderLine(models.Model):
    _inherit ='sale.order.line'

    bom_revision = fields.Char(string="Revision", compute="_onchange_bom_revision")

    def _onchange_bom_revision(self):
        for line in self:
            if line.product_id:
                bom = self.env['mrp.bom']._bom_find(product=line.product_id, company_id=line.order_id.company_id.id)
                if bom:
                    line.bom_revision = bom.bom_revision
                else:
                    line.bom_revision = "" 
            else:
                    line.bom_revision = ""   

class SaleBomLine(models.Model):
    _name = "sale.bom.line"
    _description = "Components"


    order_id = fields.Many2one(
        "sale.order",
        string="Order Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    origin_product_id = fields.Many2one(
        "product.product", string="Product", required=True, store=True
    )
    product_id = fields.Many2one(
        "product.product", string="Product Component", required=True, store=True
    )
    image_product = fields.Binary(
        "Image product", related="product_id.image_128", readonly=True
    )
    product_uom_qty = fields.Float(
        "Quantity.", digits="Product Unit of Measure", default=0.0
    )
    product_uom = fields.Many2one("uom.uom", "UoM")
    
    