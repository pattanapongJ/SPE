from . import models
from . import report
from odoo import api, SUPERUSER_ID

def _post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Update warehouse_id for all locations
    all_locations = env['stock.location'].with_context(active_test=False).search(
        [
            ('warehouse_id', '=', False),
        ]
    )
    all_locations.action_update_warehouse()