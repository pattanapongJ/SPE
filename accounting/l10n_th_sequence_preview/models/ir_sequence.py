from odoo import api, fields, models


class IrSequencePreview(models.Model):
    """
    This sub-class adds a preview field.
    """

    _inherit = "ir.sequence"

    preview = fields.Char("Preview", compute="_compute_preview")

    @api.onchange(
        "prefix",
        "suffix",
        "padding",
        "use_date_range",
        "number_next_actual",
        "implementation",
    )
    def _compute_preview(self):
        for record in self:
            if record.use_date_range:
                record.date_range_ids.onchange_sequence_id()
                record.preview = None
            else:
                record.preview = record.get_next_char(record.number_next_actual)
