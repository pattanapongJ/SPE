from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


class ResPartner(models.Model):
    _inherit = 'res.partner'

    remark_delivery = fields.Text('Remark Delivery')
    
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # note = fields.Text('Terms and conditions')
    remark_delivery = fields.Text('Remark Delivery')
    lang_code = fields.Char(string='Language Code', compute='_compute_lang_code', store=True)

    @api.onchange('partner_id', 'partner_shipping_id')
    def _onchange_remark_delivery(self):
        for order in self:
            # Check if partner_shipping_id is a delivery type child of partner_id
            remark = ''
            if order.partner_shipping_id and order.partner_id:
                if order.partner_shipping_id.parent_id == order.partner_id and order.partner_shipping_id.type == 'delivery':
                    remark = order.partner_shipping_id.remark_delivery
            # if not remark and order.partner_id:
            #     remark = order.partner_id.remark_delivery
            order.remark_delivery = remark

    @api.model
    def _default_note_en(self):
        remark_text = self.env['ir.config_parameter'].sudo().get_param('hdc_sale_remark.remark_text_en')
        return remark_text if remark_text else ''
    
    @api.model
    def _default_note_th(self):
        remark_text = self.env['ir.config_parameter'].sudo().get_param('hdc_sale_remark.remark_text_th')
        return remark_text if remark_text else ''
    
    note_th = fields.Text('Terms and conditions', default=_default_note_th)
    note_en = fields.Text('Terms and conditions', default=_default_note_en)
    
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.note_th:
            res["remark"] = self.note_th
            res["remark_report"] = self.remark_delivery
        return res
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    remark_th = fields.Boolean(string="Term and Conditions (Thai)", implied_group='sale.remark',
        help="Default Remark")
    
    remark_en = fields.Boolean(string="Term and Conditions (ENG)", implied_group='sale.remark',
        help="Default Remark")
    
    remark_text_th = fields.Text(string="Term and Conditions (Thai)")
    remark_text_en = fields.Text(string="Term and Conditions (ENG)")

    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("hdc_sale_remark.remark_text_th", self.remark_text_th)
        self.env['ir.config_parameter'].sudo().set_param("hdc_sale_remark.remark_text_en", self.remark_text_en)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        remark_text_th = self.env['ir.config_parameter'].sudo().get_param('hdc_sale_remark.remark_text_th')
        res['remark_text_th'] = remark_text_th if remark_text_th else ''
        
        remark_text_en = self.env['ir.config_parameter'].sudo().get_param('hdc_sale_remark.remark_text_en')
        res['remark_text_en'] = remark_text_en if remark_text_en else ''
        
        return res
    
