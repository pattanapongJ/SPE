
from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, format_date, OrderedSet


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    inter_type_id = fields.Many2one(
        'inventory.inter.transfer.type',
        string='Inter Transfer Type'
    )

    borrow_type_id = fields.Many2one(
        'inventory.borrow.type',
        string='Borrow Type'
    )
