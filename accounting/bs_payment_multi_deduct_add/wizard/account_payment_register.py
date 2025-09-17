# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.addons.website.tests.test_views import attrs

_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    add_gl_items = fields.Many2many(
        string=_('Add GL items'),
        comodel_name='account.move.line'
    )

    @api.onchange('add_gl_items')
    def onchange_add_gl_items(self):
        values = []
        for item in self.add_gl_items:
            _deduct_val = self.gl_prepare_deduct_line(item)
            values.append((0, 0, _deduct_val))

        if values:
            self.update({'deduction_ids': values})

        self.add_gl_items = [(5, 0, 0)]

    def gl_prepare_deduct_line(self, item):
        vals = {
            'name': item.display_name,
            'account_id': item.account_id.id,
            'open': False,
            'gl_item_id': item._origin.id,
            'amount': abs(item.balance)
        }
        ### To update default values of XML when create method is called
        for def_key,def_field in self._get_deduction_ids_context({}).items():
            if not def_key.startswith('default_'):
                continue
            _deduct_field = def_key.replace('default_','')

            if _deduct_field not in vals and def_field in self._fields:
                value = getattr(self, def_field, None)
                if value:
                    _finalize_val = value
                    if isinstance(self._fields[def_field], fields.Many2one):
                        _finalize_val = value.id
                    vals.update({def_field:_finalize_val})
        return vals

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        return payment_vals

    def _prepare_deduct_move_line(self, deduct):
        val = super(AccountPaymentRegister, self)._prepare_deduct_move_line(deduct)
        val['offset_move_line_id'] = deduct.gl_item_id.id
        return val
