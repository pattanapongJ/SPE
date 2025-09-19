from odoo import api, fields, models


class ReceiveMethod(models.Model):
    _name = "receive.method"
    _description = "receive.method"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "name"

    name = fields.Char("Receive Method", required=True)
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