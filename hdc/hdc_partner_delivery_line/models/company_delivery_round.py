# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

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
            rec_name = "%s" % (record.code)
            result.append((record.id, rec_name))
        return result