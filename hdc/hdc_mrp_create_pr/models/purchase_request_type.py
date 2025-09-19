# Copyright 2021 ProThai Technology Co.,Ltd. (http://prothaitechnology.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PurchaseRequestType(models.Model):
    _inherit =  "purchase.request.type"

    currency_id = fields.Many2one('res.currency',string='Currency')

    
