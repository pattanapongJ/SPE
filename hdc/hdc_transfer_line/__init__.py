from . import models
from . import tests

from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['stock.picking.type'].search([
        ('name', 'ilike', '%โอนสินค้า%'),
        ('is_internal_transfer', '!=', True)
    ]).write({
        'is_internal_transfer': True,
    })

