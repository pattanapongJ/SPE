# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class DeliveryRoundMaster(models.Model):
    _inherit = "delivery.round"

    name = fields.Char(string="Delivery Line")
    code = fields.Char(string="Delivery Code", required=True)
    

    def name_get(self):
        result = []
        for record in self:
            rec_name = "%s" % (record.code)
            result.append((record.id, rec_name))
        return result