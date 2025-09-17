# Copyright 2022 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _,api,fields, models

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    is_retail_type_id = fields.Boolean(related='sale_type_id.is_retail',string='Is Retail Sales Types')
    is_booth_type_id = fields.Boolean(related='sale_type_id.is_booth',string='Is Booth Sales Types')

class Quotations(models.Model):
    _inherit = 'quotation.order'

    is_retail_type_id = fields.Boolean(related='type_id.is_retail',string='Is Retail Sales Types')
    is_booth_type_id = fields.Boolean(related='type_id.is_booth',string='Is Booth Sales Types')