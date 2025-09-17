# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class DeliveryRoundMaster(models.Model):
    _name = "delivery.round"
    _description = "Delivery Round Master"

    name = fields.Char(string="Delivery Line")
    code = fields.Char(string="Delivery Code", required=True)
    driver = fields.Many2one('driver.model', string = 'Driver')
    regis_no = fields.Char(string="Car Registation")
    max_delivery_rounds = fields.Char(string="Max Delivery Round")
    start_time= fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")
    # warehouse_selection = fields.Selection([
    #     ('branch','Branch'),
    #     ('distribution_center','Distribution Center'),
    # ],string="Warehouse", required=True)
    # branch_id = fields.Many2one('res.branch',string="Branch", required=True)

    status_active = fields.Boolean(string="Active", default=True, required=True)

    @api.model
    def name_get(self):
        result = []
        for record in self:
            full_name = record.name + " - [" + record.code + "]"
            name = full_name
            result.append((record.id,name))
        return result
    
    def write(self, vals):
        for rec in self:
            delivery_trl = rec.env['delivery.round'].search([('code', '=', vals.get('code'))])
            record_id = rec._origin.id
            if delivery_trl and delivery_trl.id != record_id:
                raise UserError(_("Delivery Code ที่ระบุซ้ำกันบนระบบ กรุณาตรวจสอบอีกครั้ง"))
            res = super(DeliveryRoundMaster, rec).write(vals)
            return res

    @api.model
    def create(self, vals):
        delivery_trl = self.env['delivery.round'].search([('code', '=', vals.get('code'))])
        record_id = self._origin.id
        if delivery_trl and delivery_trl.id != record_id:
            raise UserError(_("Delivery Code ที่ระบุซ้ำกันบนระบบ กรุณาตรวจสอบอีกครั้ง"))
        res = super(DeliveryRoundMaster, self).create(vals)
        return res
    
    @api.onchange("driver")
    def _onchange_driver(self):
        if self.driver.car_registration:
            self.regis_no = self.driver.car_registration