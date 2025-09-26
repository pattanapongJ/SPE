# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    #ไม่ดึง internal notes มา
    # def _get_description(self, picking_type_id):
    #     """ return product receipt/delivery/picking description depending on
    #     picking type passed as argument.
    #     """
    #     self.ensure_one()
    #     picking_code = picking_type_id.code
    #     # description = self.description or self.name
    #     description = self.name
    #     if picking_code == 'incoming':
    #         return self.description_pickingin or self.description or description
    #     if picking_code == 'outgoing':
    #         return self.description_pickingout or self.name
    #     if picking_code == 'internal':
    #         return self.description_picking or self.description or description
    #     return description

    #ไม่เอา default code
    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
        name = self.name
        if self.description_sale:
            # name += '\n' + self.description_sale
            name = self.description_sale

        return name

class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    name = fields.Many2one(
        'res.partner', 'Vendor',
        ondelete='cascade', required=True,
        help="Vendor of this product", check_company=True, domain=[('supplier', '=', True)])

    buyer_name = fields.Char(string='Buyer Name')
    vendor_code = fields.Char(related="name.ref",string='Vendor Code')
    production_leadtime = fields.Integer(string='Production Leadtime')
    booking = fields.Integer(string='Booking')
    transit_time = fields.Integer(string='Transit Time')
    clearance = fields.Integer(string='Clearance')
    product_delivery_safety = fields.Integer(string='ProductionDelivery + Safetystock', compute="_compute_product_delivery_safety")
    safety_stock = fields.Integer(string='Safety stock')
    month_to_stock = fields.Integer(string='จำนวนเดือนที่ต้องการสั่งสินค้า To stock',compute="_compute_month_to_stock")
    remark = fields.Char(string='Remark')
    
    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):
        if self.product_tmpl_id and self.product_tmpl_id.id:
            try:
                product_ids = self.env["product.product"].search([
                    ('product_tmpl_id', '=', self.product_tmpl_id.id)
                ])
                self.update({'product_id': product_ids})
            except:
                return

    def _compute_product_delivery_safety(self):
        for rec in self:
            rec.product_delivery_safety = rec.production_leadtime + rec.booking + rec.transit_time + rec.clearance
    def _compute_month_to_stock(self):
        for rec in self:
            m_t_s = (float(rec.product_delivery_safety)+float(rec.safety_stock))/30
            if round(m_t_s - int(m_t_s), 2) >= 0.1:
                rec.month_to_stock = int(m_t_s)+1
            else:
                rec.month_to_stock = int(m_t_s)