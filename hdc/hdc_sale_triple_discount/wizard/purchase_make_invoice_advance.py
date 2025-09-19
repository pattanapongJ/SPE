# Copyright 2019 Elico Corp, Dominique K. <dominique.k@elico-corp.com.sg>
# Copyright 2019 Ecosoft Co., Ltd., Kitti U. <kittiu@ecosoft.co.th>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


# class SaleAdvancePaymentInv(models.TransientModel):
#     _inherit = "sale.advance.payment.inv"

#     def create_invoices(self):
#         sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
#         for order in sale_orders:
#             order_lines_to_invoice = order.order_line.filtered(lambda line: line.invoice_status == 'no')
#         if len(order_lines_to_invoice)>0 and sale_orders.invoice_status == 'to invoice':
#             raise UserError(("You cannot create invoice please check delivery order."))
#         return super(SaleAdvancePaymentInv, self).create_invoices()