from odoo import fields, models, api

class Addition_Operation_Type(models.Model):
    _name = "addition.operation.type"
    _description = "Addition Operation Type"

    addition_Operation_type = fields.Char("Addition Operation Type", required=True, tracking=True)
    code = fields.Char(size=6, required=True, tracking=True)
    description = fields.Char("Description", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    create_uid = fields.Many2one(
        "res.users",
        string="Created by",
        index=True,
        default=lambda self: self.env.user.id,
        tracking=2,
        readonly=1,
    )
    write_date = fields.Datetime(string="Modify Date", readonly=True)

    def name_get(self):
        """ This method used to customize display name of the record """
        result = []
        for record in self:
            rec_name = "%s" % (record.addition_Operation_type)
            result.append((record.id, rec_name))
        return result

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        recs = self.browse()
        if not recs:
            recs = self.search(
                [("addition_Operation_type", operator, name)] + args, limit=limit
            )
        return recs.name_get()
