from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
import random

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    is_vendor_dummy = fields.Boolean(string="Vendor Dummy", copy=False, default=False)
    


