# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PdcWizard(models.Model):
    _inherit = 'pdc.wizard'
    
    customer_bank_id = fields.Many2one('res.partner.bank', string='Customer Bank Account',
        compute="_compute_customer_bank_id", store=True, readonly=False)
    
    
    
    @api.depends('partner_id')
    def _compute_customer_bank_id(self):
        for rec in self:
            if rec.partner_id:
                bank_ids = rec.partner_id.bank_ids
                if bank_ids:
                    rec.customer_bank_id = bank_ids[0]
                else:
                    rec.customer_bank_id = False
            else:
                rec.customer_bank_id = False
