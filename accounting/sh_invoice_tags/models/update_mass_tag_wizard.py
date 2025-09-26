# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models, api


class updatemasstag(models.TransientModel):

    _name = "sh.update.mass.tag.wizard"
    _description = "Mass Tag Update Wizard"

    account_move_ids = fields.Many2many('account.move')
    wiz_tag_ids = fields.Many2many("sh.invoice.tags",
                                   string="Invoice Tags",
                                   required=True)
    update_method = fields.Selection([
        ("add", "Add"),
        ("replace", "Replace"),
    ],
                                     default="add")

    def update_tags(self):
        if self.update_method == 'add':
            for i in self.wiz_tag_ids:
                self.account_move_ids.write({'invoice_tag_ids': [(4, i.id)]})

        if self.update_method == 'replace':
            self.account_move_ids.write(
                {'invoice_tag_ids': [(6, 0, self.wiz_tag_ids.ids)]})
