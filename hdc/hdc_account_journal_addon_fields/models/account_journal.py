# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    sale_example = fields.Boolean(string="Sale Example")

    journal_voucher_th = fields.Char(string="Journals Voucher TH")
    journal_voucher_en = fields.Char(string="Journals Voucher EN")

    