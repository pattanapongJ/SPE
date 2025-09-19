# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    is_default_warehouse = fields.Boolean(string='Is Default Warehouse')

    @api.onchange('is_default_warehouse')
    def _is_default_warehouse_onchange(self):
        for rec in self:
            warehouse_id = rec.env['stock.warehouse'].search([('company_id', '=', rec.company_id.id),('is_default_warehouse', '=', True)])
            record_id = rec._origin.id
            if warehouse_id and warehouse_id.id != record_id and rec.is_default_warehouse == True:
                raise UserError(_("กรุณาตรวจสอบคลังสินค้าเริ่มต้นใหม่อีกครั้ง"))
        
    def write(self, vals):
        for rec in self:
            warehouse_id = rec.env['stock.warehouse'].search([('company_id', '=', rec.company_id.id),('is_default_warehouse', '=', True)])
            record_id = rec._origin.id
            if warehouse_id and warehouse_id.id != record_id and rec.is_default_warehouse == True:
                raise UserError(_("กรุณาตรวจสอบคลังสินค้าเริ่มต้นใหม่อีกครั้ง"))
            res = super(Warehouse, rec).write(vals)
            return res

    @api.model
    def create(self, vals):
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id),('is_default_warehouse', '=', True)])
        record_id = self._origin.id
        if warehouse_id and warehouse_id.id != record_id and vals.get('is_default_warehouse') == True:
            raise UserError(_("กรุณาตรวจสอบคลังสินค้าเริ่มต้นใหม่อีกครั้ง"))
        res = super(Warehouse, self).create(vals)
        return res