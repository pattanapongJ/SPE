# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_line = fields.Many2one("delivery.round", "สายส่ง TRL", domain=[('status_active', '=', True)])
    # delivery_company = fields.Many2one("company.delivery.round", string="Mode of delivery")

    # @api.onchange('delivery_line')
    # def change_delivery_line(self):
    #   if self.delivery_line:
    #     return {'domain': {'delivery_company':[('status_active', '=', True),('delivery_line', '=', self.delivery_line.id)]}}
    #   else:
    #       return {'domain': {'delivery_company':[('status_active', '=', True)]}}