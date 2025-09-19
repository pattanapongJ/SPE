# Copyright (C) 2021 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class Repair(models.Model):
    _inherit = "repair.order"

    repair_type_id = fields.Many2one(comodel_name="repair.type")
    location_id = fields.Many2one(
        compute="_compute_location_id", store=True, readonly=False
    )

    @api.depends("repair_type_id")
    def _compute_location_id(self):
        for rec in self:
            if rec.repair_type_id.source_location_id:
                rec.location_id = rec.repair_type_id.source_location_id


class RepairLine(models.Model):
    _inherit = "repair.line"

    location_id = fields.Many2one(
        compute="_compute_location_id", store=True, readonly=False
    )
    location_dest_id = fields.Many2one(
        compute="_compute_location_id", store=True, readonly=False
    )
    product_id = fields.Many2one(
        'product.product', 'Product', required=True, check_company=True,
        domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    @api.depends("type", "repair_id.repair_type_id")
    def _compute_location_id(self):
        for rec in self:
            if (
                rec.type == "add"
                and rec.repair_id.repair_type_id.source_location_add_part_id
            ):
                rec.location_id = (
                    rec.repair_id.repair_type_id.source_location_add_part_id
                )
            if (
                rec.type == "add"
                and rec.repair_id.repair_type_id.destination_location_add_part_id
            ):
                rec.location_dest_id = (
                    rec.repair_id.repair_type_id.destination_location_add_part_id
                )
            if (
                rec.type == "remove"
                and rec.repair_id.repair_type_id.source_location_remove_part_id
            ):
                rec.location_id = (
                    rec.repair_id.repair_type_id.source_location_remove_part_id
                )
            if (
                rec.type == "remove"
                and rec.repair_id.repair_type_id.destination_location_remove_part_id
            ):
                rec.location_dest_id = (
                    rec.repair_id.repair_type_id.destination_location_remove_part_id
                )

    @api.onchange("type")
    def onchange_operation_type(self):
        # this onchange was overriding the changes from the compute
        # method `_compute_location_id`, we ensure that the locations
        # in the types have more priority by explicit calling the compute.
        res = super().onchange_operation_type()
        self._compute_location_id()
        return res
    
    @api.onchange('repair_id', 'product_id', 'product_uom_qty')
    def onchange_product_id(self):
        """ On change of product it sets product quantity, tax account, name,
        uom of product, unit price and price subtotal. """
        if not self.product_id or not self.product_uom_qty:
            return
        self = self.with_company(self.company_id)
        partner = self.repair_id.partner_id
        partner_invoice = self.repair_id.partner_invoice_id or partner
        if partner:
            self = self.with_context(lang=partner.lang)
        product = self.product_id
        # self.name = product.display_name
        # if product.description_sale:
        #     if partner:
        #         self.name += '\n' + self.product_id.with_context(lang=partner.lang).description_sale
        #     else:
        #         self.name += '\n' + self.product_id.description_sale

        self.name = self.product_id.description_sale

        self.product_uom = product.uom_id.id
        if self.type != 'remove':
            if partner:
                fpos = self.env['account.fiscal.position'].get_fiscal_position(partner_invoice.id, delivery_id=self.repair_id.address_id.id)
                taxes = self.product_id.taxes_id.filtered(lambda x: x.company_id == self.repair_id.company_id)
                self.tax_id = fpos.map_tax(taxes, self.product_id, partner).ids
            warning = False
            pricelist = self.repair_id.pricelist_id
            if not pricelist:
                warning = {
                    'title': _('No pricelist found.'),
                    'message':
                        _('You have to select a pricelist in the Repair form !\n Please set one before choosing a product.')}
                return {'warning': warning}
            else:
                self._onchange_product_uom()
