# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _,api,fields, models


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    description = fields.Char(string="Description", help="Description of the sequence")

    def name_get(self):
        result = []
        for seq in self:
            if seq.preview:
                display_name = f"{seq.name} ({seq.preview})"
            else:
                display_name = seq.name
            result.append((seq.id, display_name))
        return result
