from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
    
class Picking(models.Model):
    _inherit = 'stock.picking'
    
    sales_type_id = fields.Many2one(related = 'sale_id.type_id',depends = ["sale_id"], store = True,string="Sales Type")

    