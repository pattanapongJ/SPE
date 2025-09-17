# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sub_district = fields.Char(string="Sub-District")
    @api.depends("zip_id")
    def _compute_city(self):
        super()._compute_city()
        for record in self:
            if record.zip_id and record.country_id.code == "TH":
                address = record.zip_id.city_id.name.split(", ")
                record.update({"sub_district": address[0], "city": address[1]})
