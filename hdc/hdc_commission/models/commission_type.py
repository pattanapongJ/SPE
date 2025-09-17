from odoo import api, fields, models

class CommissionType(models.Model):
    _name = "commission.type"
    _description = "Commission Type"

    name = fields.Char(string = "Display Name", required=True, tracking = True)
    code = fields.Char(string = "Code", required=True, tracking = True)
    description = fields.Char(string = "Description", tracking = True)
    is_active = fields.Boolean(string ="Active", tracking = True)

    def name_get(self):
        result = []
        for record in self:
            rec_name = '['+ record.code + ']' + record.name
            result.append((record.id, rec_name))
        return result