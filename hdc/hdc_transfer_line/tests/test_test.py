import cProfile, pstats

from odoo.tests import common
from odoo.addons.test.utils import timing
from odoo.tools.profiler import profile
from odoo.addons.stock.models import product

class Test(common.TransactionCase):

    def test_01(self):
        print('test_01.self ', self)
        lines = self.env['hdc.transfer.line'].search([('move_id', '=', 264244)])
        print(lines)
        print(lines.mapped('picking_id'))
        
