# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ZortLogs(models.Model):
    _name = "zort.logs"
    _description = "ZORT Logs"
    _order = "id desc"

    name = fields.Char(string = "Name", copy=False)
    log_note = fields.Text(string = "Log Sale Order", copy=False)
    app_list = fields.Many2one('zort.app.list', string="Apps list", copy=False)
    state = fields.Selection(selection = [("success", "Success"),
                                          ("error", "Error")],
                             string = "Status", readonly = True )
    description = fields.Text(string = "Description", copy=False)


