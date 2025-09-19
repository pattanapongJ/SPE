# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SubLocations(models.Model):
    _name = 'sub.locations'
    _description = "Sub Locations"

    name = fields.Char(string="Sub location Name", required=True)
    location_id = fields.Many2one('stock.location', string="Location", required=True)
    product_id = fields.Many2one('product.product', string="Product", required=True)   
    is_default = fields.Boolean(string="Is Default Sub Location", default=False)

    @api.constrains('is_default')
    def _check_default(self):
        for record in self:
            if record.is_default:
                default = self.search([('product_id', '=', record.product_id.id),('is_default', '=', True), ('id', '!=', record.id)])
                if default:
                    raise UserError(_("ไม่สามารถระบุ Default Sub Location พร้อมกันหลายที่จัดเก็บได้ กรุณาตรวจสอบอีกครั้ง."))

class StockPutawayRule(models.Model):
    _inherit = 'stock.putaway.rule'

    sub_location_id = fields.Many2one('sub.locations', string="Sub Location")

    def button_add_sub(self):
        for rec in self:
            if not rec.sub_location_id:
                rec.sub_location_id = self.env['sub.locations'].search([('product_id', '=', rec.product_id.id), ('location_id', '=', rec.location_out_id.id),
                                                                        ('is_default', '=', True)], limit=1)