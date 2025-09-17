# -*- coding: utf-8 -*-
import logging

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DateRange(models.Model):
    _inherit = 'date.range'

    month_th = fields.Selection(selection=[("01", "มกราคม"),
                                           ("02", "กุมภาพันธ์"),
                                           ("03", "มีนาคม"),
                                           ("04", "เมษายน"),
                                           ("05", "พฤษภาคม"),
                                           ("06", "มิถุนายน"),
                                           ("07", "กรกฎาคม"),
                                           ("08", "สิงหาคม"),
                                           ("09", "กันยายน"),
                                           ("10", "ตุลาคม"),
                                           ("11", "พฤศจิกายน"),
                                           ("12", "ธันวาคม")], string=_('Month(TH)'))
    year_th = fields.Char(string=_('Year(TH)'))

    def _get_month_thai(self):
        if not self.month_th:
            return '-'
        return dict(self._fields['month_th'].selection).get(self.month_th)
