# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import hashlib
import itertools
import logging
import mimetypes
import os
import re
from collections import defaultdict
import uuid

from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError, ValidationError, MissingError, UserError
from odoo.tools import config, human_size, ustr, html_escape
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.onchange("datas")
    def onchange_datas(self):
        if self.name:
            if not self.name.split(".")[-1] in ["pdf", "GIF", "png", "jpg", "jpeg"]:
                raise UserError(_("กรุณาเลือกไฟล์ pdf, JPG, JEPG, GIF, PNG"))

    def write(self, vals):
        self.check("write", values=vals)
        # remove computed field depending of datas
        for field in ("file_size", "checksum"):
            vals.pop(field, False)

        if "mimetype" in vals or "datas" in vals:
            vals = self._check_contents(vals)
        if "file_size" in vals:
            if vals.get("file_size") > 5242880:
                raise ValidationError(_("ขนาดไฟล์ไม่เกิน 5MB"))

        return super(IrAttachment, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        record_tuple_set = set()
        for values in vals_list:
            # remove computed field depending of datas
            for field in ("file_size", "checksum"):
                values.pop(field, False)
            values = self._check_contents(values)
            if "datas" in values:
                data = values.pop("datas")
                values.update(
                    self._get_datas_related_values(
                        base64.b64decode(data or b""), values["mimetype"]
                    )
                )
                if "file_size" in values:
                    if values.get("file_size") > 5242880:
                        raise ValidationError(_("ขนาดไฟล์ไม่เกิน 5MB"))
            # 'check()' only uses res_model and res_id from values, and make an exists.
            # We can group the values by model, res_id to make only one query when
            # creating multiple attachments on a single record.
            record_tuple = (values.get("res_model"), values.get("res_id"))
            record_tuple_set.add(record_tuple)
        for record_tuple in record_tuple_set:
            (res_model, res_id) = record_tuple
            self.check("create", values={"res_model": res_model, "res_id": res_id})
        return super(IrAttachment, self).create(vals_list)