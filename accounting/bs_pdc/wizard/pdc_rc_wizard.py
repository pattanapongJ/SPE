# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PdcRcWizard(models.TransientModel):
    _name = 'pdc.rc.wizard'
    _description = _('PdcRcWizard')

    pdc_id = fields.Many2one(
        string=_('PDC'),
        comodel_name='pdc.wizard',
        required=True
    )
    journal_id = fields.Many2one(
        string=_('Journal'),
        comodel_name='account.journal',
        required=True
    )

    @api.onchange("pdc_id")
    def onchange_pdc_id(self):
        journal_type = 'sale' if self.pdc_id.payment_type == 'receive_money' else 'purchase'
        domain = [("type", "=", journal_type)]
        return {"domain": {"journal_id": domain}}

    def action_create_journal_entry(self):
        _entry_val = self._prepare_entry_val()
        entry_id = self.env['account.move'].create(_entry_val)
        if entry_id:
            self.pdc_id.write({'state':'rc'})
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = entry_id.id
        return action

    def _prepare_entry_val(self):
        self.ensure_one()
        vals = {
            'pdc_id': self.pdc_id.id,
            'move_type': 'out_invoice' if self.pdc_id.payment_type == 'receive_money' else 'in_invoice',
            'currency_id': self.pdc_id.currency_id.id,
            'user_id': self.env.user.id,
            'partner_id': self.pdc_id.partner_id.id,
            'journal_id': self.journal_id.id,
            'invoice_line_ids': self._prepare_entry_line_val(),
            'company_id': self.env.company.id,
        }
        return vals

    def _prepare_entry_line_val(self):
        account_id = self._get_account_id()
        val = {
            'name': account_id.name,
            'quantity': 1,
            'price_unit': self.pdc_id.payment_amount,
            'pdc_id': self.pdc_id.id,
            'account_id': account_id.id
        }
        return [(0, 0, val)]

    def _get_account_id(self):
        account_id = self.pdc_id.company_id.pdc_customer if self.pdc_id.payment_type == 'receive_money' else self.pdc_id.company_id.pdc_vendor
        if self.pdc_id.state == 'done':
            account_id = self.pdc_id.journal_id.payment_debit_account_id if self.pdc_id.payment_type == 'receive_money' else self.pdc_id.journal_id.payment_credit_account_id
            
        return account_id
