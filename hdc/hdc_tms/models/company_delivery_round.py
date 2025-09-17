# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class CompanyDeliveryRoundMaster(models.Model):
    _name = "company.delivery.round"
    _description = "Company Delivery Round Master"

    name = fields.Char(string="Company Delivery Line")
    code = fields.Char(string="Code", required=True)
    delivery_line = fields.Many2one("delivery.round", string="Delivery Line")
    status_active = fields.Boolean(string="Active", default=True, required=True)


    def name_get(self):
        result = []
        for record in self:
            rec_name = record.code + " ("+ record.name + ")"
            result.append((record.id, rec_name))
        return result
    
    def write(self, vals):
        for rec in self:
            delivery_company = rec.env['company.delivery.round'].search([('code', '=', vals.get('code'))])
            record_id = rec._origin.id
            if delivery_company and delivery_company.id != record_id:
                raise UserError(_("Code ที่ระบุซ้ำกันบนระบบ กรุณาตรวจสอบอีกครั้ง"))
            res = super(CompanyDeliveryRoundMaster, rec).write(vals)
            return res

    @api.model
    def create(self, vals):
        delivery_company = self.env['company.delivery.round'].search([('code', '=', vals.get('code'))])
        record_id = self._origin.id
        if delivery_company and delivery_company.id != record_id:
            raise UserError(_("Code ที่ระบุซ้ำกันบนระบบ กรุณาตรวจสอบอีกครั้ง"))
        res = super(CompanyDeliveryRoundMaster, self).create(vals)
        return res