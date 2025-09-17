from itertools import chain
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.exceptions import AccessError, UserError
from odoo.exceptions import Warning
from datetime import datetime, timedelta

class CostPricelist(models.Model):
    _name = "cost.pricelist"
    _description = "Cost Pricelists"

    _sql_constraints = [
        ("cost_pricelist_uniq", "unique (product_id)", "A must be unique product !",)]

    product_id = fields.Many2one('product.product', string = 'Product', required=True)
    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id', string = 'Product Template')
    pricelist_type = fields.Selection(related='product_tmpl_id.source', string="Pricelist Type")
    current_sale_price = fields.Float(string = 'Current Sale Price', digits=(16, 2))
    po_cost = fields.Float(string = 'PO Cost', digits=(16, 2))
    pricelist_config = fields.Many2one("pricelist.configuration", string = 'Pricelist')
    exchange_rate = fields.Float(related='pricelist_config.exchange_rate')
    taxes = fields.Float(related='pricelist_config.taxes')
    margin = fields.Float(related='pricelist_config.margin')
    surcharge = fields.Float(related='pricelist_config.surcharge')
    fright = fields.Float(related='pricelist_config.fright')
    frist_discount = fields.Float(related='pricelist_config.frist_discount')
    sec_discount = fields.Float(related='pricelist_config.sec_discount')
    std_price = fields.Float(string = 'Calc Price',compute='_compute_std_price', digits = (16, 2))
    last_updated = fields.Datetime(string = 'Last Updated')
    status = fields.Selection(
        [("normal", "Normal"),
         ("change", "Change")],
         string="Status", readonly=True)
    update_price = fields.Float(string = 'Update Price', digits = (16, 2))

    @api.onchange('current_sale_price', 'po_cost', 'std_price','product_id')
    def onchange_product_id(self):
        value = self.pricelist_config.variant * self.po_cost
        self.status = "normal"
        self.update_price = value

    
    @api.depends('current_sale_price','po_cost','pricelist_config.variant')
    def _compute_std_price(self):
        for price_list in self:
            value = price_list.pricelist_config.variant * price_list.po_cost
            price_list.std_price = value

    @api.model
    def create(self, vals):
        res = super(CostPricelist, self).create(vals)
        product_tmpl = res.product_tmpl_id
        supplierinfos = self.env['product.supplierinfo'].search([
            ('id', 'in', product_tmpl.seller_ids.ids)
        ], order='create_date desc', limit=1)

        if supplierinfos.price :
            res.po_cost = supplierinfos.price
        res.current_sale_price = product_tmpl.product_variant_id.lst_price
        # res.std_price = product_tmpl.product_variant_id.lst_price
        
        return res

    def update_price_button(self):
        self.last_updated = datetime.now()
        self.status = "change"
        self.current_sale_price = self.update_price
        self.product_id.lst_price = self.update_price
        self.product_id.standard_price = self.update_price

class CostPricelistConfiguration(models.Model):
    _name = "pricelist.configuration"
    _description = "Pricelist Configuration"

    name = fields.Char(string = 'Pricelist Name', required =True)
    cate_id = fields.Many2one('product.category', string = 'Product Category')
    brand = fields.Many2one("product.brand", string = 'Brand')
    currency_id = fields.Many2one("res.currency", string = "Currency",  required = False, )
    exchange_rate = fields.Float(string = 'Exchange Rate', digits = (16, 2), required =True)
    taxes = fields.Float(string = 'Taxes', digits = (16, 2), required =True)
    margin = fields.Float(string = 'Margin', digits = (16, 2), required =True)
    surcharge = fields.Float(string = 'Surcharge', digits = (16, 2), required =True)
    fright = fields.Float(string = 'Fright', digits = (16, 2), required =True)
    frist_discount = fields.Float(string = 'First Discount', digits = (16, 2), required =True)
    sec_discount = fields.Float(string = 'Sec Discount', digits = (16, 2), required =True)
    variant = fields.Float(string = 'Variant',compute="_compute_variant", digits = (16, 2))

    def _compute_variant(self):
        for rec in self:
            try:
                value = (rec.exchange_rate*rec.taxes*rec.surcharge*rec.fright*rec.margin)/(rec.frist_discount*rec.sec_discount)
                rec.variant = value
            except:
                rec.variant = 0.0

class PricelistType(models.Model):
    _name = "pricelist.type"
    _description = "Pricelist Type"

    
    factor = fields.Float(string = 'Factor', digits = (16, 2), required =True)
    pricelist_type = fields.Selection([
            ("inter", "International"), 
            ("domestic", "Domestic"),
        ],
        string="Pricelist Type", required =True)
    active = fields.Boolean(string = 'Status', default=True)
    name = fields.Char(string='Name', compute='_compute_name', store=True)

    @api.depends('pricelist_type')
    def _compute_name(self):
        for record in self:
            record.name = dict(self._fields['pricelist_type'].selection).get(record.pricelist_type)


    @api.model
    def create(self, vals):
        
        # Check if a record with the same 'pricelist_type' value already exists
        existing_record = self.search([('pricelist_type', '=', vals.get('pricelist_type')),('active','=',True)])
        if existing_record:
            raise ValidationError('Pricelist type must be unique!')
        res = super(PricelistType, self).create(vals)
        return res
    