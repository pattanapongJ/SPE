# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PdcWizard(models.Model):
    _inherit = 'pdc.wizard'
    
    
    drawer = fields.Char(string='Drawer',copy=False)
    # bank_account_holder_id = fields.Many2one('res.partner', 'Bank Account Holder', ondelete='cascade', index=True,copy=False, domain=['|', ('is_company', '=', True), ('parent_id', '=', False)])
    bank_account_holder_id = fields.Many2one(related='customer_bank_id.partner_id',store=True)
    no_of_signature = fields.Integer('Number of Signature',copy=False)

    @api.onchange('journal_id')
    def onchange_bank_journal_id(self):
        if self.journal_id:
            self.bank_id = self.journal_id.bank_account_id.bank_id
            self.bank_branch = self.journal_id.bank_account_id.bank_branch



    def action_register(self):
        self._check_cheque_ref_and_bank()
        super(PdcWizard,self).action_register()


    def _check_cheque_ref_and_bank(self):
        if self.reference and self.bank_id:
            usages = self.env['pdc.wizard'].search_count([('reference','=',self.reference),('bank_id','=',self.bank_id.id),('id','!=',self.id)])
            if usages > 0:
                raise ValidationError(_('The combination of Cheque Number and Bank already exists'))









