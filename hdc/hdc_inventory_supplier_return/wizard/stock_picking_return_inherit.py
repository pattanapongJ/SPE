from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round



class ReturnPickingInherit(models.TransientModel):
    _inherit = 'stock.return.picking'
