# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResExtIDUpadte(models.Model):
    _name = "res.ext.id.update"
    _order = "date desc"
    _description = "External ID Report"

    name = fields.Char("Subject", required=True)
    date = fields.Datetime("Date")
    user_id = fields.Many2one("res.users", "Update by")
    obj_id = fields.Many2one("base.synchro.obj", "Object", ondelete="cascade")
    body = fields.Text("Request")
