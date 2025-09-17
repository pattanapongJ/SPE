from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.exceptions import UserError
from odoo.exceptions import Warning


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    is_master_key_product = fields.Boolean(string="Is Master Key")
    is_master_key_service = fields.Boolean(string="Is Master Key Service")
    is_master_key_dummy = fields.Boolean(string="Is Dummy Master Key")