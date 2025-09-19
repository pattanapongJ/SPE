from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class ProductPricelistCustomer(models.Model):
    _name = "product.pricelist.customer"
    _description = "Product Pricelist Customer"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        domain="[('customer_rank','>', 0)]",
        required=True ,index=True
    )
    pricelist_id = fields.Many2one(
        'product.pricelist', 'Pricelist',
        help="This pricelist will be used, instead of the default one, for sales to the current partner" ,index=True)
    phone = fields.Char(related='partner_id.phone',index=True)
    email = fields.Char(related='partner_id.email' ,index=True)
    user_id = fields.Many2one(related='partner_id.user_id' ,index=True)
    city = fields.Char(related='partner_id.city' ,index=True)
    country_id = fields.Many2one(related='partner_id.country_id' ,index=True)
    vat = fields.Char(related='partner_id.vat' ,index=True)
    category_id = fields.Many2many(related='partner_id.category_id' ,index=True)
    company_id = fields.Many2one(related='partner_id.company_id' ,index=True)
    is_default = fields.Boolean(string='Default Pricelist')

    @api.onchange('is_default')
    def _onchange_is_default(self):
        for record in self:
            check_default = self.search([('partner_id', '=', record.partner_id.id),('pricelist_id','!=',record.pricelist_id.id),('is_default','=',True)],limit=1)
            if check_default:
                record.is_default = False
                language = self.env.context.get('lang')
                if language == 'th_TH':
                    raise ValidationError(_("ไม่สามารถเลือกได้ เนื่องจาก %s ได้ตั้งค่าไว้แล้ว กรุณาไปเอาออกก่อน", check_default.pricelist_id.name))
                else:
                    raise ValidationError(_("Cannot be selected because %s has already been set. Please go remove it first.", check_default.pricelist_id.name))
            else :
                record.partner_id.property_product_pricelist = record.pricelist_id

    @api.constrains('partner_id')
    def _check_partner_uniqueness(self):
        for record in self:
            if record.partner_id:
                existing_records = self.search([('partner_id', '=', record.partner_id.id), ('id', '!=', record.id),('pricelist_id','=',record.pricelist_id.id)])
                if existing_records:
                    language = self.env.context.get('lang')
                    if language == 'th_TH':
                        raise ValidationError(_("ไม่สามารถเลือกลูกค้าซ้ำได้!"))
                    else:
                        raise ValidationError(_("Partner must be unique in Product Pricelist Customer!"))


class ResPartner(models.Model):
    _inherit = "res.partner"

    pricelist_ids = fields.Many2many(
        comodel_name='product.pricelist',string='Pricelist', compute="_compute_pricelist_ids", 
        help="This pricelist will be used, instead of the default one, for sales to the current partner")
    
    def _compute_pricelist_ids(self):
        for partner in self:
            pricelist_records = self.env["product.pricelist.customer"].search([
                ('partner_id', '=', partner.id)
            ])
            linked_pricelist_ids = pricelist_records.mapped('pricelist_id')
            all_pricelists = self.env['product.pricelist'].search([
                ('pricelist_all', '=', True)
            ])
            additional_pricelists = all_pricelists.filtered(
                lambda p: p.id not in linked_pricelist_ids.ids
            )
            partner.pricelist_ids = linked_pricelist_ids | additional_pricelists
