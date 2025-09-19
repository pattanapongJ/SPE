# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class CrmClaimEpt(models.Model):
    _inherit = "crm.claim.ept"

    ref_sale_rma = fields.Char(string="Ref. Sale RMA")