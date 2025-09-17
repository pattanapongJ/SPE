# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from collections import defaultdict

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    show_update_pricelist = fields.Boolean(string = 'Has Pricelist Changed',
                                           help = "Technical Field, True if the pricelist was changed;\n"
                                                  " this will then display a recomputation button")

    @api.onchange('pricelist_id')
    def _onchange_pricelist_to_change_fiscal_position_id(self):
        if len(self.ref_sale_id) == 0:
            self.currency_id = self.pricelist_id.currency_id.id
            fiscal_position_ids = self.env.company.fiscal_position_id
            fiscal_position = False
            if len(fiscal_position_ids) > 0:
                for order in self:
                    for fiscal in fiscal_position_ids:
                        for tax_ids in fiscal.tax_ids:
                            if tax_ids.tax_dest_id.price_include == True:
                                fiscal_position = fiscal
                                break
                        if fiscal_position != False:
                            break
                    if fiscal_position == False:
                        fiscal_position = fiscal_position_ids[0]
                    order.fiscal_position_id = fiscal_position
            if fiscal_position == False:
                if self.line_ids and self.pricelist_id and self._origin.pricelist_id != self.pricelist_id:
                    self.show_update_pricelist = True
                else:
                    self.show_update_pricelist = False
                for order in self:
                    fiscal_position_id = order.pricelist_id.fiscal_position_id
                    if fiscal_position_id:
                        order.fiscal_position_id = fiscal_position_id
            
            self.onchange_partner_shipping_id()

    @api.onchange('partner_shipping_id', 'partner_id', 'company_id')
    def onchange_partner_shipping_id(self):
        fiscal_position_ids = self.env.company.fiscal_position_id
        fiscal_position = False
        if len(fiscal_position_ids) > 0:
            for order in self:
                for fiscal in fiscal_position_ids:
                    for tax_ids in fiscal.tax_ids:
                        if tax_ids.tax_dest_id.price_include == True:
                            fiscal_position = fiscal
                            break
                    if fiscal_position != False:
                        break
                if fiscal_position == False:
                    fiscal_position = fiscal_position_ids[0]
                order.fiscal_position_id = fiscal_position
        
        if self.partner_id.property_account_position_id:
            customer_fiscal_position_id = self.env['account.fiscal.position'].with_company(self.company_id).get_fiscal_position(self.partner_id.id, self.partner_shipping_id.id)
        else:
            customer_fiscal_position_id = False

        if customer_fiscal_position_id:
            if customer_fiscal_position_id.id != self.fiscal_position_id.id:
                self.fiscal_position_id = customer_fiscal_position_id.id
        return {}