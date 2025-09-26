# Copyright 2019 Elico Corp, Dominique K. <dominique.k@elico-corp.com.sg>
# Copyright 2019 Ecosoft Co., Ltd., Kitti U. <kittiu@ecosoft.co.th>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class WizardBlanketOrderChangeTotal(models.TransientModel):
    _name = "wizard.blanket.orders.change.total"
    _description = 'wizard blanket orders change total'

    order_id = fields.Many2one('sale.blanket.order', string='Sale Agreement')
    rounding_untax = fields.Char(string='Rounding Untaxed Amount')
    rounding_taxes = fields.Char(string='Rounding Taxes')
    rounding_total = fields.Char(string='Rounding Total')
    
    def update_blanket_orders_total(self):
        decimal_precision = self.env['decimal.precision'].precision_get('Sale Rounding')
        rounding_pattern = re.compile(r'^[+-]?\d+(\.\d{1,%d})?$' % decimal_precision)
        rounding_fields = {
            'rounding_untax': self.rounding_untax,
            'rounding_taxes': self.rounding_taxes,
            'rounding_total': self.rounding_total,
        }
        
        for field_name, value in rounding_fields.items():
            if value:
                if not rounding_pattern.match(value):
                    raise ValidationError(_('Invalid Rounding format for %s: +20 or -20 with up to %d decimal places' % (field_name.replace('_', ' '), decimal_precision)))
                setattr(self.order_id, field_name, value)
            else:
                setattr(self.order_id, field_name, False)
        