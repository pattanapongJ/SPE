from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.exceptions import UserError
from odoo.exceptions import Warning


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _description = "Product Template"
    
    free_product = fields.Boolean(string="Free Product")

