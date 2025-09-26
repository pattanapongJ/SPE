from odoo import models, fields, api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)

class RecordDeletionLog(models.Model):
    _name = "record.deletion.log"
    _description = "Record Deletion Log"
    _order = "create_date desc"

    name = fields.Char("Name/Description")
    model = fields.Char("Model")
    res_id = fields.Integer("Record ID")
    deleted_by = fields.Many2one("res.users", string="Deleted By")

class RecordDeletionLogSetting(models.Model):
    _name = "record.deletion.log.setting"
    _description = "Record Deletion Log Settings"

    name = fields.Char(string="Name", required=True)
    model_id = fields.Many2one('ir.model', string="Model", required=True, ondelete="cascade")
    active_log = fields.Boolean(string="Active", default=True)
    
class BaseModel(models.AbstractModel):
    _inherit = "base"

    def unlink(self):
        records = self
        user = self.env.user

        active_settings = self.env['record.deletion.log.setting'].sudo().search([('active_log','=',True)])
        active_model_names = active_settings.mapped('model_id.model')

        for rec in records:
            if rec._name in active_model_names:
                try:
                    self.env["record.deletion.log"].sudo().create({
                        "name": getattr(rec, "name", str(rec.id)),
                        "model": rec._name,
                        "res_id": rec.id,
                        "deleted_by": user.id,
                    })
                except Exception as e:
                    _logger.error("Error logging deletion for %s: %s", rec, e)

        return super(BaseModel, records).unlink()