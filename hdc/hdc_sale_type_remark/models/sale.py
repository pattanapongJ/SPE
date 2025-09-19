from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


from odoo import api, fields, models


class SaleOrderTypology(models.Model):
    _inherit = "sale.order.type"

    remark_oversea = fields.Text(string="Remark Oversea")
    show_remark_oversea = fields.Boolean(string="Show Remark Oversea",default=False)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    remark_oversea = fields.Text(related="type_id.remark_oversea",string="Remark Oversea")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    remark_oversea_th = fields.Boolean(string="Remark Oversea", implied_group='sale.remark_oversea',
        help="Default Remark Oversea")

    remark_oversea_text_th = fields.Text(
            string="Default Remark Oversea",
            default="""PAYMENT:TT100%inAdvance
    BENEFICIARY:SAENGCHAROENPATANAENTERPRISECO.,LTD.
    BANKNAME:KASIKORNBANKPUBLICCOMPANYLIMITED
    BANKADDRESS:40022PhahonYothinRoadSamsenNai,Phayathai,Bangkok10400,Thailand
    SWIFT:KASITHBK
    ACNO:016-1-04615-9""",
            help="Default remark text for oversea transactions"
        )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("hdc_sale_type_remark.remark_oversea_text_th", self.remark_oversea_text_th)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        remark_oversea_text_th = self.env['ir.config_parameter'].sudo().get_param('hdc_sale_type_remark.remark_oversea_text_th')
        res['remark_oversea_text_th'] = remark_oversea_text_th if remark_oversea_text_th else ''
        return res
    
