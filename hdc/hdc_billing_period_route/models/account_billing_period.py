from odoo import api, fields, models

class BillingPeriodRoute(models.Model):
    _name = "account.billing.period"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Char(string="Description")

    def name_get(self):
        result = []
        for record in self:
            rec_name = record.name
            result.append((record.id, rec_name))
        return result
