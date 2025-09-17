from odoo import api, fields, models

class BillingPeriodRoute(models.Model):
    _name = "account.billing.route"

    name = fields.Char(string="Code", required=True)
    label = fields.Char(string="Name")
    description = fields.Char(string="Description")

    def name_get(self):
        result = []
        for record in self:
            description = record.description if record.description else ""
            rec_name = record.name + " ( " + description + " )"
            result.append((record.id, rec_name))
        return result

    